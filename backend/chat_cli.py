"""
Command-line chat interface for the NLIP performance stress-testing chatbot.

This file handles user input, wraps chat messages as NLIP messages,
runs the stress-testing pipeline, and prints results in the terminal.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Optional, Union
from . import ollama_input, pipeline
from .config import _project_root
from .data_conversion import validate_json
from nlip.nlip_sdk.nlip_sdk.nlip import NLIP_Factory, NLIP_Message


def ensure_nlip_message(message: Union[str, dict[str, Any], NLIP_Message], *, speaker: str, conversation_token: Optional[str] = None) -> NLIP_Message:
    """Normalize a message into an NLIP message, adding a conversation token if provided."""
    if isinstance(message, NLIP_Message):
        return message
    if isinstance(message, dict):
        msg = NLIP_Factory.create_json(
            message,
            label=speaker.lower(),
            messagetype="Response",
        )
    else:
        msg = NLIP_Factory.create_text(
            str(message),
            label=speaker.lower(),
            messagetype="Response",
        )

    if conversation_token:
        msg.add_conversation_token(conversation_token, label="conversation")
    return msg


def print_chat_message(speaker: str, message: Union[str, dict[str, Any], NLIP_Message], *, conversation_token: Optional[str] = None) -> NLIP_Message:
    """Print a chat message after wrapping it in NLIP."""
    nlip_message = ensure_nlip_message(message, speaker=speaker, conversation_token=conversation_token)
    print(f"{speaker}: {ollama_input.nlip_to_text(nlip_message)}")
    return nlip_message


def read_user_message(prompt: str, *, conversation_token: Optional[str] = None) -> NLIP_Message:
    """Read one user terminal response as an NLIP request message."""
    return ollama_input.get_user_response(prompt, conversation_token=conversation_token, label="user")


def extract_response_content(message: Union[str, NLIP_Message]) -> Any:
    """Extract JSON from a response when possible, otherwise return the response text."""
    text = ollama_input.nlip_to_text(message)
    extracted = ollama_input.extract_json(text)
    if extracted:
        try:
            return json.loads(extracted)
        except json.JSONDecodeError:
            pass
    return {"updated_result": text}


def chat_cli() -> None:
    """Main function to run the chat CLI."""
    conversation_token = ollama_input.new_conversation_token() # Start a new conversation for this session

    print_chat_message("System", "Hi, I am your performance stress testing agent.", conversation_token=conversation_token)
    print_chat_message("System", "Please describe the system you want to analyze.", conversation_token=conversation_token)

    _, system_description_path = ollama_input.ask_sys_desc(conversation_token=conversation_token)
    system_description_file = Path(system_description_path).name

    print_chat_message(
        "System",
        "Thank you for providing the system description. I will now analyze it and generate insights.",
        conversation_token=conversation_token,
    )

    result = pipeline.pipeline(system_description_file)
    status = result.get("status") if isinstance(result, dict) else None

    if status == "needs_clarification":
        print_chat_message("System", "I need some more information before I can continue.", conversation_token=conversation_token)
        print_chat_message("System", {"context": result.get("context")}, conversation_token=conversation_token)
    elif status == "error":
        print_chat_message("System", "I found an error when processing your system description:", conversation_token=conversation_token)
        print_chat_message("System", {"errors": result.get("errors")}, conversation_token=conversation_token)
    else:
        print_chat_message("System", "Here are the insights I generated based on your system description:", conversation_token=conversation_token)
        print_chat_message("System", result if isinstance(result, dict) else {"result": result}, conversation_token=conversation_token)

        # Ask if the user needs any clarification on the results of the analysis.
        question = "Do you have any questions about the insights I provided, or is there anything you'd like me to clarify?"
        print_chat_message("System", question, conversation_token=conversation_token)
        user_response = ollama_input.get_user_response("Ask any questions/clarifications you have, or only type 'no' to end the conversation:", conversation_token=conversation_token)

        # Continue to handle follow-up questions until the user indicates they have no more questions.
        while ollama_input.nlip_to_text(user_response).strip().lower() != "no":
            follow_up_response = ollama_input.handle_follow_up_answer(user_response, question=question, system_desc=system_description_file, analysis_result=result, conversation_token=conversation_token)
            print_chat_message("System", follow_up_response, conversation_token=conversation_token)
            print_chat_message("System", "Do you have any other questions or clarifications?", conversation_token=conversation_token)
            user_response = ollama_input.get_user_response("Ask any questions/clarifications you have, or only type 'no' to end the conversation:", conversation_token=conversation_token)
        
        print_chat_message("System", "All files have been saved to the data folder and stress test analysis has completed, ending conversation...", conversation_token=conversation_token)