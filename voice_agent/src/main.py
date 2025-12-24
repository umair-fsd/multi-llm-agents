"""
Voice Agent Service - Main Entry Point

Multi-agent voice interaction with full conversation tracking.
"""

import asyncio
import logging
import os

from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    AgentSession,
    Agent,
)
from livekit.plugins import openai, silero, deepgram

from src.config import (
    LIVEKIT_API_KEY,
    LIVEKIT_API_SECRET,
    LIVEKIT_URL,
    OPENAI_API_KEY,
    DEEPGRAM_API_KEY,
)
from src.db import agent_db_service
from src.db.session_history import session_history_service
from src.llm import MultiAgentLLM

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global VAD instance (preloaded in prewarm)
_vad: silero.VAD | None = None


def prewarm(proc):
    """Prewarm function to preload models."""
    global _vad
    logger.info("Prewarming: Loading Silero VAD model...")
    _vad = silero.VAD.load()
    logger.info("Prewarming complete: Silero VAD loaded")


async def entrypoint(ctx: JobContext):
    """Main entrypoint for handling LiveKit room connections."""
    logger.info(f"=== NEW SESSION: Room {ctx.room.name} ===")
    
    session_id = None
    agents_used = set()
    tools_used_in_session = set()
    
    try:
        # Connect to room
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
        logger.info("Connected to LiveKit room")
        
        # Wait for participant
        participant = await ctx.wait_for_participant()
        participant_name = participant.identity
        logger.info(f"Participant joined: {participant_name}")
        
        # Load ALL active agents from database
        agents = await agent_db_service.get_all_agents()
        
        if not agents:
            logger.warning("No agents found in database, using default")
            agents = [{
                'id': None,
                'name': 'Assistant',
                'system_prompt': 'You are a helpful AI assistant.',
                'model_settings': {},
                'capabilities': {},
            }]
        
        logger.info(f"Loaded {len(agents)} agents: {[a['name'] for a in agents]}")
        default_agent = agents[0]
        
        # Create session in database with participant info
        try:
            session_id = await session_history_service.create_session(
                room_name=ctx.room.name,
                participant_name=participant_name,
                metadata={
                    "available_agents": [a['name'] for a in agents],
                },
            )
            logger.info(f"Created session: {session_id}")
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
        
        # Use preloaded VAD
        global _vad
        if _vad is None:
            logger.warning("VAD not preloaded, loading now...")
            _vad = silero.VAD.load()
        
        # Create voice components - Use Deepgram for faster STT if available
        if DEEPGRAM_API_KEY and DEEPGRAM_API_KEY != "your-deepgram-api-key-here":
            try:
                stt = deepgram.STT()  # ~300ms vs OpenAI's ~500ms
                logger.info("Using Deepgram STT (faster)")
            except Exception as e:
                logger.warning(f"Deepgram STT failed, falling back to OpenAI: {e}")
                stt = openai.STT()
                logger.info("Using OpenAI STT (fallback)")
        else:
            stt = openai.STT()
            logger.info("Using OpenAI STT")
        
        # TTS - OpenAI with streaming
        tts = openai.TTS(voice="alloy")  # alloy is fastest voice
        
        # Create MultiAgentLLM with all agents
        multi_agent_llm = MultiAgentLLM(
            agents=agents,
            model="gpt-4o-mini",
            api_key=OPENAI_API_KEY,
        )
        
        # Track agent switches and tools
        current_agent_name = default_agent['name']
        current_agent_id = default_agent.get('id')
        last_tools_used = []
        
        def on_agent_switch(old_agent, new_agent):
            nonlocal current_agent_name, current_agent_id
            current_agent_name = new_agent
            agents_used.add(new_agent)
            # Find agent ID
            for a in agents:
                if a['name'] == new_agent:
                    current_agent_id = a.get('id')
                    break
            logger.info(f"🔄 Agent switched: {old_agent} → {new_agent}")
        
        multi_agent_llm.on_agent_switch(on_agent_switch)
        agents_used.add(current_agent_name)
        
        # Create the LiveKit Agent
        agent = Agent(
            instructions=default_agent['system_prompt'],
        )
        
        # Create AgentSession
        session = AgentSession(
            vad=_vad,
            stt=stt,
            llm=multi_agent_llm,
            tts=tts,
        )
        
        # Event: User speech transcribed - save to DB
        @session.on("user_input_transcribed")
        def on_transcribed(ev):
            if ev.is_final and session_id:
                logger.info(f"🎤 User: {ev.transcript}")
                asyncio.create_task(
                    session_history_service.add_message(
                        session_id=session_id,
                        role="user",
                        content=ev.transcript,
                        agent_id=None,
                        agent_name=None,
                        tools_used=None,
                    )
                )
        
        # Event: Conversation item added - save assistant responses to DB
        @session.on("conversation_item_added")
        def on_conversation_item(ev):
            if not session_id:
                return
            try:
                item = ev.item
                role = getattr(item, 'role', None)
                
                # Only save assistant messages (user messages saved via transcription)
                if role == "assistant":
                    content = getattr(item, 'text', None) or getattr(item, 'content', None)
                    if content:
                        content_str = str(content)
                        # Get tools used from the last LLM call
                        tools = list(multi_agent_llm._last_tools_used) if hasattr(multi_agent_llm, '_last_tools_used') else []
                        for t in tools:
                            tools_used_in_session.add(t)
                        
                        logger.info(f"🤖 [{current_agent_name}]: {content_str[:50]}... (tools: {tools})")
                        asyncio.create_task(
                            session_history_service.add_message(
                                session_id=session_id,
                                role="assistant",
                                content=content_str,
                                agent_id=current_agent_id,
                                agent_name=current_agent_name,
                                tools_used=tools,
                            )
                        )
            except Exception as e:
                logger.error(f"Error saving assistant message: {e}")
        
        # Event: Error
        @session.on("error")
        def on_error(ev):
            logger.error(f"❌ Session error: {ev.error}")
        
        # Event: Session closed
        @session.on("close")
        def on_close(ev):
            logger.info(f"Session closed: {ev.reason}")
            if session_id:
                asyncio.create_task(
                    session_history_service.end_session(
                        session_id, 
                        reason=str(ev.reason) if ev.reason else "participant_disconnect"
                    )
                )
                # Update session metadata with summary
                asyncio.create_task(
                    session_history_service.update_session_metadata(
                        session_id,
                        {
                            "agents_used": list(agents_used),
                            "tools_used": list(tools_used_in_session),
                        }
                    )
                )
        
        # Start the session
        logger.info("Starting agent session...")
        await session.start(agent, room=ctx.room)
        logger.info("✅ Agent session started!")
        
        # Send greeting and save to DB
        agent_count = len(agents)
        if agent_count > 1:
            greeting = f"Hello! I'm your AI assistant with {agent_count} specialized agents. How can I help?"
        else:
            greeting = f"Hello! I'm {default_agent['name']}. How can I help?"
        
        logger.info(f"Sending greeting: {greeting}")
        await session.say(greeting)
        
        # Save greeting to history
        if session_id:
            await session_history_service.add_message(
                session_id=session_id,
                role="assistant",
                content=greeting,
                agent_id=current_agent_id,
                agent_name=current_agent_name,
                tools_used=[],
            )
        
        logger.info("🎙️ Voice session active - waiting for user input...")
        
    except Exception as e:
        logger.exception(f"Error in entrypoint: {e}")
        if session_id:
            await session_history_service.end_session(session_id, reason=f"error: {str(e)}")
        raise


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            api_key=LIVEKIT_API_KEY,
            api_secret=LIVEKIT_API_SECRET,
            ws_url=LIVEKIT_URL,
        )
    )
