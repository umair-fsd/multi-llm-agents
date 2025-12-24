"""
Voice Agent Service - Main Entry Point

This service connects to LiveKit and provides multi-agent voice interaction.
It uses an orchestrator to dynamically route user queries to specialized agents.
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
from livekit.plugins import openai, silero

from src.config import (
    LIVEKIT_API_KEY,
    LIVEKIT_API_SECRET,
    LIVEKIT_URL,
    OPENAI_API_KEY,
)
from src.db import agent_db_service
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
    """
    Prewarm function to preload models before jobs arrive.
    """
    global _vad
    logger.info("Prewarming: Loading Silero VAD model...")
    _vad = silero.VAD.load()
    logger.info("Prewarming complete: Silero VAD loaded")


async def entrypoint(ctx: JobContext):
    """
    Main entrypoint for handling LiveKit room connections.
    """
    logger.info(f"=== NEW SESSION: Room {ctx.room.name} ===")
    
    try:
        # Connect to room
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
        logger.info("Connected to LiveKit room")
        
        # Wait for participant
        participant = await ctx.wait_for_participant()
        logger.info(f"Participant joined: {participant.identity}")
        
        # Load ALL active agents from database
        agents = await agent_db_service.get_all_agents()
        
        if not agents:
            logger.warning("No agents found in database, using default")
            agents = [{
                'id': 'default',
                'name': 'Assistant',
                'system_prompt': 'You are a helpful AI assistant.',
                'model_settings': {},
                'capabilities': {},
            }]
        
        logger.info(f"Loaded {len(agents)} agents: {[a['name'] for a in agents]}")
        
        # Get the default agent for initial greeting
        default_agent = agents[0]
        
        # Use preloaded VAD
        global _vad
        if _vad is None:
            logger.warning("VAD not preloaded, loading now...")
            _vad = silero.VAD.load()
        
        # Create voice components
        stt = openai.STT()
        tts = openai.TTS(voice="alloy")
        
        # Create MultiAgentLLM with all agents
        multi_agent_llm = MultiAgentLLM(
            agents=agents,
            model="gpt-4o-mini",
            api_key=OPENAI_API_KEY,
        )
        
        # Track agent switches
        current_agent_name = default_agent['name']
        
        def on_agent_switch(old_agent, new_agent):
            nonlocal current_agent_name
            current_agent_name = new_agent
            logger.info(f"🔄 Agent switched: {old_agent} → {new_agent}")
        
        multi_agent_llm.on_agent_switch(on_agent_switch)
        
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
        
        # Event: User speech transcribed
        @session.on("user_input_transcribed")
        def on_transcribed(ev):
            if ev.is_final:
                logger.info(f"🎤 User: {ev.transcript}")
        
        # Event: Error
        @session.on("error")
        def on_error(ev):
            logger.error(f"❌ Session error: {ev.error}")
        
        # Event: Session closed
        @session.on("close")
        def on_close(ev):
            logger.info(f"Session closed: {ev.reason}")
        
        # Start the session
        logger.info("Starting agent session...")
        await session.start(agent, room=ctx.room)
        logger.info("✅ Agent session started!")
        
        # Send greeting
        agent_count = len(agents)
        if agent_count > 1:
            greeting = f"Hello! I'm your AI assistant with access to {agent_count} specialized agents. How can I help you today?"
        else:
            greeting = f"Hello! I'm {default_agent['name']}. How can I help you today?"
        
        logger.info(f"Sending greeting: {greeting}")
        await session.say(greeting)
        
        logger.info("🎙️ Voice session active - waiting for user input...")
        
    except Exception as e:
        logger.exception(f"Error in entrypoint: {e}")
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
