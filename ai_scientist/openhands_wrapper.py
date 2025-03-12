"""
OpenHands wrapper for AI-Scientist.

This module provides a wrapper around OpenHands that mimics the aider interface
used in the AI-Scientist codebase.
"""

import asyncio
import os
from typing import List, Optional, Any

from openhands.controller.state.state import State
from openhands.core.config import AppConfig, AgentConfig
from openhands.core.main import create_runtime, run_controller
from openhands.events.action import MessageAction
from openhands.events.serialization.event import event_to_dict
from openhands.utils.async_utils import call_async_from_sync
from openhands.agenthub.codeact_agent.codeact_agent import CodeActAgent
from openhands.llm.llm import LLM
from openhands.llm.llm_config import LLMConfig


class OpenHandsCoder:
    """
    A wrapper around OpenHands that mimics the aider Coder interface.
    """

    def __init__(
        self,
        main_model: str,
        fnames: List[str],
        io: Any = None,
        stream: bool = False,
        use_git: bool = False,
        edit_format: str = "diff",
    ):
        """
        Initialize the OpenHandsCoder.

        Args:
            main_model: The model to use (can be a model name or a model object)
            fnames: List of filenames to edit
            io: Input/output object (not used in OpenHands)
            stream: Whether to stream output (not used in OpenHands)
            use_git: Whether to use git (not used in OpenHands)
            edit_format: The edit format to use (not used in OpenHands)
        """
        self.model_name = main_model
        if isinstance(main_model, str):
            self.model_name = main_model
        else:
            # Handle aider Model object
            self.model_name = main_model.name

        self.fnames = fnames
        self.chat_history_file = None
        if io and hasattr(io, "chat_history_file"):
            self.chat_history_file = io.chat_history_file

        # Initialize OpenHands components
        self.llm_config = self._create_llm_config()
        self.llm = LLM(self.llm_config)
        self.agent_config = AgentConfig(
            codeact_enable_jupyter=False,
            codeact_enable_browsing=False,
            codeact_enable_llm_editor=True,
        )
        self.agent = CodeActAgent(self.llm, self.agent_config)
        
        self.app_config = AppConfig(
            default_agent="CodeActAgent",
            run_as_openhands=False,
            max_iterations=50,  # Reasonable default
            runtime="local",
            workspace_base=os.getcwd(),
        )
        self.app_config.set_llm_config(self.llm_config)
        self.app_config.set_agent_config(self.agent_config)
        
        self.runtime = create_runtime(self.app_config)
        call_async_from_sync(self.runtime.connect)

    def _create_llm_config(self) -> LLMConfig:
        """
        Create an LLM configuration based on the model name.
        
        Returns:
            LLMConfig: The LLM configuration
        """
        # Map aider model names to OpenHands model names
        model_mapping = {
            "gpt-4": "gpt-4",
            "gpt-4o": "gpt-4o",
            "gpt-4o-2024-05-13": "gpt-4o",
            "gpt-3.5-turbo": "gpt-3.5-turbo",
            "claude-3-5-sonnet-20240620": "claude-3-5-sonnet",
            "claude-3-opus-20240229": "claude-3-opus",
            "claude-3-sonnet-20240229": "claude-3-sonnet",
            "claude-3-haiku-20240307": "claude-3-haiku",
        }
        
        # Get the mapped model name or use the original if not in the mapping
        model = model_mapping.get(self.model_name, self.model_name)
        
        # Determine provider based on model name
        provider = "openai"
        if "claude" in model.lower():
            provider = "anthropic"
        elif "llama" in model.lower():
            provider = "openrouter"
        elif "deepseek" in model.lower():
            provider = "deepseek"
            
        return LLMConfig(
            provider=provider,
            model=model,
            api_key=os.environ.get(f"{provider.upper()}_API_KEY"),
            temperature=0.7,
        )

    def run(self, prompt: str) -> str:
        """
        Run the OpenHands agent with the given prompt.
        
        Args:
            prompt: The prompt to send to the agent
            
        Returns:
            str: The agent's response
        """
        # Create a message action with the prompt
        initial_user_action = MessageAction(content=prompt)
        
        # Run the controller
        state: Optional[State] = asyncio.run(
            run_controller(
                config=self.app_config,
                initial_user_action=initial_user_action,
                runtime=self.runtime,
                agent=self.agent,
                exit_on_message=True,
            )
        )
        
        if state is None:
            return "Error: Failed to run OpenHands agent"
        
        # Extract the agent's response from the state
        response = self._extract_response(state)
        
        # Save chat history if a file was provided
        if self.chat_history_file and state.history:
            self._save_chat_history(state)
            
        return response

    def _extract_response(self, state: State) -> str:
        """
        Extract the agent's response from the state.
        
        Args:
            state: The agent's state
            
        Returns:
            str: The agent's response
        """
        # Get the last message from the agent
        for event in reversed(state.history):
            if event.source == "AGENT" and hasattr(event, "content"):
                return event.content
        
        return "No response from agent"

    def _save_chat_history(self, state: State) -> None:
        """
        Save the chat history to a file.
        
        Args:
            state: The agent's state
        """
        if not self.chat_history_file:
            return
            
        # Convert events to a serializable format
        history = [event_to_dict(event) for event in state.history]
        
        # Write to the chat history file
        os.makedirs(os.path.dirname(self.chat_history_file), exist_ok=True)
        with open(self.chat_history_file, "w") as f:
            for event in history:
                f.write(f"{event}\n")


def create_openhands_coder(
    main_model: str,
    fnames: List[str],
    io: Any = None,
    stream: bool = False,
    use_git: bool = False,
    edit_format: str = "diff",
) -> OpenHandsCoder:
    """
    Create an OpenHandsCoder instance.
    
    This function mimics the aider Coder.create() function.
    
    Args:
        main_model: The model to use
        fnames: List of filenames to edit
        io: Input/output object (not used in OpenHands)
        stream: Whether to stream output (not used in OpenHands)
        use_git: Whether to use git (not used in OpenHands)
        edit_format: The edit format to use (not used in OpenHands)
        
    Returns:
        OpenHandsCoder: An OpenHandsCoder instance
    """
    return OpenHandsCoder(
        main_model=main_model,
        fnames=fnames,
        io=io,
        stream=stream,
        use_git=use_git,
        edit_format=edit_format,
    )