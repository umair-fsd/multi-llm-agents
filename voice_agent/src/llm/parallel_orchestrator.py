"""
Parallel Agent Orchestrator - Decomposes complex queries and runs multiple agents concurrently.
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Task:
    """A decomposed task from the user query."""
    query: str
    agent_name: str
    agent_id: str
    priority: int = 0


@dataclass  
class TaskResult:
    """Result from executing a task."""
    task: Task
    response: str
    tools_used: list[str]
    success: bool
    error: Optional[str] = None


class ParallelOrchestrator:
    """
    Orchestrates parallel execution of multiple agents for complex queries.
    
    Flow:
    1. Analyze query to detect if it contains multiple distinct tasks
    2. Decompose into separate tasks
    3. Route each task to the best agent
    4. Execute all agents in parallel
    5. Aggregate results into a coherent response
    """
    
    # Conjunctions that often indicate multiple tasks
    MULTI_TASK_INDICATORS = [
        ' and ', ' also ', ' plus ', ' as well as ',
        ' additionally ', ' along with ', ' together with ',
        '. also ', '. and ', ', and ',
    ]
    
    # Task type patterns for quick detection
    TASK_PATTERNS = {
        'weather': [r'weather\s+(?:in|for|of|at)\s+(\w+)', r'temperature\s+(?:in|of)\s+(\w+)'],
        'contact': [r'contact\s+(?:number|info|details)', r'phone\s+(?:number|of)', r'call\s+'],
        'booking': [r'book\s+(?:a|the)?', r'reserve\s+', r'reservation\s+'],
        'price': [r'price\s+(?:of|for)', r'cost\s+(?:of|for)', r'how\s+much'],
        'location': [r'where\s+is', r'address\s+(?:of|for)', r'location\s+(?:of|for)'],
        'hours': [r'(?:open|opening|business)\s+hours', r'when\s+(?:is|does)\s+\w+\s+open'],
        'info': [r'tell\s+me\s+about', r'what\s+is', r'who\s+is', r'information\s+(?:about|on)'],
    }
    
    def __init__(self, agents: list[dict], agent_keywords: dict[str, set]):
        """
        Initialize the orchestrator.
        
        Args:
            agents: List of agent configurations
            agent_keywords: Mapping of agent names to their routing keywords
        """
        self.agents = agents
        self.agent_keywords = agent_keywords
        self._agents_by_name = {a['name']: a for a in agents}
    
    def needs_parallel_execution(self, query: str) -> bool:
        """
        Quick check if query might need parallel agent execution.
        
        Args:
            query: User's query
            
        Returns:
            True if query likely contains multiple distinct tasks
        """
        query_lower = query.lower()
        
        # Check for multi-task indicators
        for indicator in self.MULTI_TASK_INDICATORS:
            if indicator in query_lower:
                # Verify there are actually different task types
                task_types = self._detect_task_types(query_lower)
                if len(task_types) > 1:
                    return True
        
        return False
    
    def _detect_task_types(self, query: str) -> set[str]:
        """Detect what types of tasks are in the query."""
        detected = set()
        for task_type, patterns in self.TASK_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    detected.add(task_type)
                    break
        return detected
    
    def decompose_query(self, query: str) -> list[Task]:
        """
        Decompose a complex query into separate tasks.
        
        Args:
            query: User's query
            
        Returns:
            List of tasks, each assigned to an agent
        """
        tasks = []
        query_lower = query.lower()
        
        # Split by conjunctions
        segments = self._split_by_conjunctions(query)
        
        if len(segments) <= 1:
            # Single task - just route to best agent
            agent = self._route_to_agent(query)
            tasks.append(Task(
                query=query,
                agent_name=agent['name'],
                agent_id=agent.get('id', ''),
                priority=0,
            ))
        else:
            # Multiple segments - route each to best agent
            for i, segment in enumerate(segments):
                segment = segment.strip()
                if not segment or len(segment) < 5:
                    continue
                    
                agent = self._route_to_agent(segment)
                tasks.append(Task(
                    query=segment,
                    agent_name=agent['name'],
                    agent_id=agent.get('id', ''),
                    priority=i,
                ))
        
        # Log decomposition
        if len(tasks) > 1:
            logger.info(f"🔀 Decomposed query into {len(tasks)} parallel tasks:")
            for t in tasks:
                logger.info(f"   → [{t.agent_name}]: {t.query[:50]}...")
        
        return tasks
    
    def _split_by_conjunctions(self, query: str) -> list[str]:
        """Split query by conjunctions while preserving meaning."""
        # Use regex to split by common conjunctions
        pattern = r'\s+and\s+(?=(?:the|what|where|how|tell|get|find|show)\s+)'
        segments = re.split(pattern, query, flags=re.IGNORECASE)
        
        if len(segments) == 1:
            # Try splitting by comma + and
            pattern2 = r',\s*and\s+'
            segments = re.split(pattern2, query, flags=re.IGNORECASE)
        
        if len(segments) == 1:
            # Try splitting by period
            segments = [s.strip() for s in query.split('.') if s.strip()]
        
        return segments
    
    def _route_to_agent(self, query: str) -> dict:
        """Route a query segment to the best agent."""
        query_lower = query.lower()
        
        # Score each agent
        scores = {}
        for agent in self.agents:
            keywords = self.agent_keywords.get(agent['name'], set())
            score = sum(1 for kw in keywords if kw in query_lower)
            scores[agent['name']] = score
        
        # Find best match
        best_name = max(scores, key=scores.get) if scores else self.agents[0]['name']
        
        # If no keywords matched, use default agent
        if scores.get(best_name, 0) == 0:
            return self.agents[0]
        
        return self._agents_by_name.get(best_name, self.agents[0])
    
    async def execute_parallel(
        self,
        tasks: list[Task],
        execute_fn,
    ) -> list[TaskResult]:
        """
        Execute multiple tasks in parallel.
        
        Args:
            tasks: List of tasks to execute
            execute_fn: Async function to execute a single task
                       Signature: async def execute_fn(task: Task) -> TaskResult
                       
        Returns:
            List of results in same order as tasks
        """
        if not tasks:
            return []
        
        if len(tasks) == 1:
            # Single task, no need for parallelism
            result = await execute_fn(tasks[0])
            return [result]
        
        logger.info(f"⚡ Executing {len(tasks)} agents in parallel...")
        
        # Execute all tasks concurrently
        results = await asyncio.gather(
            *[execute_fn(task) for task in tasks],
            return_exceptions=True,
        )
        
        # Process results
        task_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                task_results.append(TaskResult(
                    task=tasks[i],
                    response="",
                    tools_used=[],
                    success=False,
                    error=str(result),
                ))
            else:
                task_results.append(result)
        
        successful = sum(1 for r in task_results if r.success)
        logger.info(f"✅ Parallel execution complete: {successful}/{len(tasks)} successful")
        
        return task_results
    
    def aggregate_results(self, results: list[TaskResult]) -> str:
        """
        Aggregate multiple task results into a coherent response.
        
        Args:
            results: List of task results
            
        Returns:
            Combined response string
        """
        if not results:
            return "I couldn't process your request."
        
        if len(results) == 1:
            return results[0].response if results[0].success else "I encountered an error."
        
        # Combine successful results
        responses = []
        for result in results:
            if result.success and result.response:
                responses.append(result.response.strip())
        
        if not responses:
            return "I encountered errors processing your requests."
        
        # Join with appropriate connector
        if len(responses) == 2:
            return f"{responses[0]} Also, {responses[1].lower()}" if responses[1][0].isupper() else f"{responses[0]} Also, {responses[1]}"
        else:
            return " ".join(responses)
    
    def get_all_tools_used(self, results: list[TaskResult]) -> list[str]:
        """Get combined list of all tools used across results."""
        tools = set()
        for result in results:
            tools.update(result.tools_used)
        return list(tools)
    
    def get_all_agents_used(self, results: list[TaskResult]) -> list[str]:
        """Get list of all agents used."""
        return list(set(r.task.agent_name for r in results))

