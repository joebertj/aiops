"""
AI Agents for AIOps System

This module contains specialized agents that process prompts in series before they reach the main AI.
Each agent is responsible for specific domains and can intercept, modify, or handle prompts directly.

Agent Processing Order:
1. Security Agent - Validates and filters potentially dangerous operations
2. Kubernetes Agent - Handles Kubernetes-related prompts using direct API calls
3. Container Agent - Handles container operations using runc (Docker-compatible)
4. Command Router Agent - Routes between Bash and AI based on command detection

All agents implement the Agent interface and process prompts in a chain with fail-fast behavior.
If any agent fails, processing stops immediately and the user is informed.
"""

from .base_agent import BaseAgent
from .security_agent import SecurityAgent
from .process_agent import ProcessAgent
from .kubernetes_agent import KubernetesAgent
from .container_agent import ContainerAgent
from .command_router_agent import CommandRouterAgent
from .response_parser import ResponseParser, ParsedResponse, ResponseMode
from .agent_processor import AgentProcessor

__all__ = [
    'BaseAgent',
    'SecurityAgent',
    'ProcessAgent',  # Add process monitoring agent
    'KubernetesAgent',
    'ContainerAgent',
    'CommandRouterAgent',
    'ResponseParser',
    'ParsedResponse',
    'ResponseMode',
    'AgentProcessor'
]
