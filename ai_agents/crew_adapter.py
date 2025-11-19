# ai_agents/crew_adapter.py
import asyncio
from typing import Callable, Any, List, Dict

class AgentInterface:
    def __init__(self, name: str, run_fn: Callable[[str, Dict[str,Any]], Any]):
        self.name = name
        self._run_fn = run_fn

    async def a_run(self, user_input: str, context: Dict[str, Any] | None = None):
        return await asyncio.to_thread(self._run_fn, user_input, context or {})

    def run(self, user_input: str, context: Dict[str, Any] | None = None):
        return self._run_fn(user_input, context or {})

def make_agent(name: str, run_fn: Callable[[str, Dict[str,Any]], Any]) -> AgentInterface:
    return AgentInterface(name, run_fn)

class Crew:
    def __init__(self, agents: List[AgentInterface]):
        self.agents = {a.name: a for a in agents}

    async def a_run_agent(self, agent_name: str, user_input: str, context: Dict[str, Any] | None = None):
        agent = self.agents.get(agent_name)
        if not agent:
            raise KeyError(f"Agent not found: {agent_name}")
        return await agent.a_run(user_input, context or {})

    def run_agent(self, agent_name: str, user_input: str, context: Dict[str, Any] | None = None):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            fut = asyncio.run_coroutine_threadsafe(self.a_run_agent(agent_name, user_input, context or {}), loop)
            return fut.result()
        else:
            return asyncio.run(self.a_run_agent(agent_name, user_input, context or {}))
