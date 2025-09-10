"""
Agent Processor for AIOps System

Manages the series processing of agents with fail-fast behavior.
If any agent fails, processing stops immediately and the user is informed.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from .base_agent import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


class AgentProcessor:
    """
    Processes prompts through a series of agents with fail-fast behavior.
    
    Agent Processing Flow:
    1. Security Agent (priority 10) - Validates safety and filters sensitive data
    2. Kubernetes Agent (priority 20) - Handles Kubernetes operations
    3. Container Agent (priority 30) - Handles container operations using runc
    4. Command Router Agent (priority 100) - Routes between Bash and AI
    
    If any agent fails, processing stops immediately and the user is informed.
    """
    
    def __init__(self, agents: List[BaseAgent]):
        """
        Initialize the agent processor.
        
        Args:
            agents: List of agents to process prompts through (sorted by priority)
        """
        self.agents = sorted(agents, key=lambda x: x.priority)
        self.agent_names = [agent.name for agent in self.agents]
        
        logger.info(f"Initialized AgentProcessor with {len(self.agents)} agents:")
        for agent in self.agents:
            logger.info(f"  - {agent.name} (priority: {agent.priority})")
    
    async def process_prompt(self, prompt: str, context: Dict[str, Any]) -> Tuple[bool, str, Optional[str], Dict[str, Any]]:
        """
        Process a prompt through the agent series with fail-fast behavior.
        
        Args:
            prompt: User's input prompt
            context: Additional context (working directory, user, etc.)
            
        Returns:
            Tuple of (success, response, modified_prompt, metadata)
            - success: True if processing completed successfully
            - response: Response to show user (error message if failed)
            - modified_prompt: Modified prompt to pass to next stage (None if failed)
            - metadata: Processing metadata
        """
        logger.info(f"Processing prompt through {len(self.agents)} agents: '{prompt[:50]}...'")
        
        current_prompt = prompt
        processing_metadata = {
            "original_prompt": prompt,
            "agents_processed": [],
            "agents_failed": [],
            "processing_stages": []
        }
        
        try:
            # Process through each agent in priority order
            for i, agent in enumerate(self.agents):
                logger.debug(f"Processing with agent {i+1}/{len(self.agents)}: {agent.name}")
                
                try:
                    # Check if agent should handle this prompt
                    if not agent.should_handle(current_prompt, context):
                        logger.debug(f"Agent {agent.name} skipped prompt (should_handle=False)")
                        processing_metadata["agents_processed"].append({
                            "agent": agent.name,
                            "action": "skipped",
                            "reason": "should_handle=False"
                        })
                        continue
                    
                    # Process with agent
                    result = await agent.process(current_prompt, context)
                    
                    # Record processing stage
                    stage_info = {
                        "agent": agent.name,
                        "priority": agent.priority,
                        "handled": result.handled,
                        "action": result.metadata.get("security_action", "processed") if result.metadata else "processed"
                    }
                    processing_metadata["processing_stages"].append(stage_info)
                    processing_metadata["agents_processed"].append(agent.name)
                    
                    # Check if agent handled the prompt (returned a response)
                    if result.handled:
                        logger.info(f"Agent {agent.name} handled prompt with response")
                        return True, result.response, None, processing_metadata
                    
                    # Agent didn't handle, but may have modified the prompt
                    if result.modified_prompt is not None:
                        current_prompt = result.modified_prompt
                        logger.debug(f"Agent {agent.name} modified prompt")
                    
                    # If agent provided a response but didn't handle, show it to user
                    if result.response:
                        logger.info(f"Agent {agent.name} provided response but didn't handle prompt")
                        return True, result.response, current_prompt, processing_metadata
                    
                    logger.debug(f"Agent {agent.name} passed prompt through unchanged")
                    
                except Exception as e:
                    # Agent failed - stop processing immediately
                    error_msg = f"❌ **AGENT FAILURE** ❌\n\n"
                    error_msg += f"Agent '{agent.name}' failed while processing your prompt.\n\n"
                    error_msg += f"**Error:** {str(e)}\n\n"
                    error_msg += f"**Processing stopped at:** {agent.name} (priority {agent.priority})\n\n"
                    error_msg += f"**Original prompt returned:** {prompt}\n\n"
                    error_msg += f"**Recommendations:**\n"
                    error_msg += f"• Check your prompt for any issues\n"
                    error_msg += f"• Try rephrasing your request\n"
                    error_msg += f"• Contact support if the issue persists\n\n"
                    error_msg += f"**Processing details:**\n"
                    error_msg += f"• Agents processed: {', '.join(processing_metadata['agents_processed'])}\n"
                    error_msg += f"• Failed agent: {agent.name}\n"
                    
                    logger.error(f"Agent {agent.name} failed: {e}", exc_info=True)
                    
                    processing_metadata["agents_failed"].append({
                        "agent": agent.name,
                        "error": str(e),
                        "stage": i + 1
                    })
                    
                    return False, error_msg, prompt, processing_metadata
            
            # All agents processed successfully, no one handled the prompt
            logger.info("All agents processed successfully, prompt passed through")
            return True, None, current_prompt, processing_metadata
            
        except Exception as e:
            # Unexpected error in processor itself
            error_msg = f"❌ **PROCESSOR FAILURE** ❌\n\n"
            error_msg += f"An unexpected error occurred in the agent processor.\n\n"
            error_msg += f"**Error:** {str(e)}\n\n"
            error_msg += f"**Original prompt returned:** {prompt}\n\n"
            error_msg += f"**Recommendations:**\n"
            error_msg += f"• Try again with a simpler prompt\n"
            error_msg += f"• Check system logs for more details\n"
            error_msg += f"• Contact support if the issue persists\n"
            
            logger.error(f"AgentProcessor failed: {e}", exc_info=True)
            
            processing_metadata["processor_error"] = str(e)
            return False, error_msg, prompt, processing_metadata
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get status information about all agents.
        
        Returns:
            Dictionary with agent status information
        """
        return {
            "total_agents": len(self.agents),
            "agent_list": [
                {
                    "name": agent.name,
                    "priority": agent.priority,
                    "help": agent.get_help()
                }
                for agent in self.agents
            ],
            "processing_order": [agent.name for agent in self.agents]
        }
    
    def get_agent_by_name(self, name: str) -> Optional[BaseAgent]:
        """
        Get an agent by name.
        
        Args:
            name: Agent name
            
        Returns:
            Agent instance or None if not found
        """
        for agent in self.agents:
            if agent.name == name:
                return agent
        return None
    
    async def cleanup(self):
        """
        Cleanup all agents that support cleanup.
        """
        for agent in self.agents:
            if hasattr(agent, 'cleanup') and callable(agent.cleanup):
                try:
                    await agent.cleanup()
                    logger.debug(f"Cleaned up agent: {agent.name}")
                except Exception as e:
                    logger.error(f"Failed to cleanup agent {agent.name}: {e}")
    
    def add_agent(self, agent: BaseAgent):
        """
        Add a new agent to the processor.
        
        Args:
            agent: Agent to add
        """
        self.agents.append(agent)
        self.agents.sort(key=lambda x: x.priority)
        self.agent_names = [agent.name for agent in self.agents]
        logger.info(f"Added agent: {agent.name} (priority: {agent.priority})")
    
    def remove_agent(self, name: str) -> bool:
        """
        Remove an agent by name.
        
        Args:
            name: Agent name to remove
            
        Returns:
            True if agent was removed, False if not found
        """
        for i, agent in enumerate(self.agents):
            if agent.name == name:
                removed_agent = self.agents.pop(i)
                self.agent_names = [agent.name for agent in self.agents]
                logger.info(f"Removed agent: {removed_agent.name}")
                return True
        return False
