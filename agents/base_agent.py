"""
Base Agent Interface for AIOps System

All agents must implement this interface to participate in the prompt processing chain.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class AgentResult:
    """Result from agent processing"""
    handled: bool  # Whether this agent handled the prompt
    response: Optional[str] = None  # Response if handled
    modified_prompt: Optional[str] = None  # Modified prompt to pass to next agent
    metadata: Optional[Dict[str, Any]] = None  # Additional metadata


class BaseAgent(ABC):
    """
    Base class for all AIOps agents.
    
    Agents process prompts in series, with each agent having the opportunity to:
    1. Handle the prompt completely (return response)
    2. Modify the prompt and pass it along
    3. Pass the prompt unchanged to the next agent
    """
    
    def __init__(self, name: str, priority: int = 0):
        """
        Initialize the agent.
        
        Args:
            name: Human-readable name of the agent
            priority: Processing priority (lower numbers process first)
        """
        self.name = name
        self.priority = priority
    
    @abstractmethod
    def should_handle(self, prompt: str, context: Dict[str, Any]) -> bool:
        """
        Determine if this agent should handle the given prompt.
        
        Args:
            prompt: The user's input prompt
            context: Additional context (current directory, previous commands, etc.)
            
        Returns:
            True if this agent should handle the prompt
        """
        pass
    
    @abstractmethod
    async def process(self, prompt: str, context: Dict[str, Any]) -> AgentResult:
        """
        Process the prompt and return a result.
        
        Args:
            prompt: The user's input prompt
            context: Additional context
            
        Returns:
            AgentResult indicating how the prompt was handled
        """
        pass
    
    def get_help(self) -> str:
        """
        Get help text for this agent.
        
        Returns:
            Help text describing what this agent does
        """
        return f"{self.name} agent - {self.__class__.__doc__ or 'No description available'}"
    
    def __lt__(self, other):
        """Enable sorting by priority"""
        return self.priority < other.priority
    
    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}', priority={self.priority})"
