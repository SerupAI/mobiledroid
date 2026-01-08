"""Wrapper for the agent module."""

import sys
import os

# Add lib/agent/src to path for local development
# In Docker, it's already in PYTHONPATH
if not os.path.exists("/app"):  # Not in Docker
    agent_path = os.path.join(os.path.dirname(__file__), "../../../lib/agent/src")
    if agent_path not in sys.path:
        sys.path.insert(0, agent_path)

# Now we can import directly
from agent import MobileDroidAgent, AgentConfig

__all__ = ["MobileDroidAgent", "AgentConfig"]