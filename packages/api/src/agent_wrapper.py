"""Wrapper for the agent module to fix import paths."""

import sys
import os

# In Docker, the agent is at /app/agent_src/src
# In development, it's at ../../agent/src
if os.path.exists("/app/agent_src"):
    # Docker environment
    sys.path.insert(0, "/app/agent_src")
    from src.agent import MobileDroidAgent, AgentConfig
else:
    # Development environment
    agent_path = os.path.join(os.path.dirname(__file__), "../../agent/src")
    sys.path.insert(0, agent_path)
    from agent import MobileDroidAgent, AgentConfig

__all__ = ["MobileDroidAgent", "AgentConfig"]