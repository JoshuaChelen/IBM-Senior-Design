"""
Command-line chat interface for the NLIP performance stress-testing chatbot.

This file handles user input, wraps chat messages as NLIP messages,
runs the stress-testing pipeline, and prints results in the terminal.
"""

from __future__ import annotations
import json
import time
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


# def follow_up(system_desc: dict[str, Any], validation_result: dict[str, Any], *, conversation_token: Optional[str] = None) -> Optional[str]:
#     """
#     Generate and ask one follow-up question to get clarification and 
#     missing info from user, then update sys desc based on that.
#     """
#     conversation_token = conversation_token or ollama_input.new_conversation_token()

#     missing_info = validation_result.get("needs_clarification", [])
#     issues = validation_result.get("errors", [])

#     prompt = f"""
#     Given this system description:
#     {system_desc}

#     The validation step identified the following gaps:
#     Needs Clarification: {missing_info}
#     Issues: {issues}

#     Generate ONE follow-up question to ask the user that would help fill in the missing information and/or address the issues.
#     The question should be clear and concise, and should directly relate to the gaps identified in the validation step.
#     """.strip()

#     question_nlip = ollama_input.ask_follow_up(prompt, conversation_token=conversation_token, return_nlip=True)
#     print_chat_message("System", question_nlip, conversation_token=conversation_token)

#     answer_nlip = read_user_message("Input your answer to the follow-up question:", conversation_token=conversation_token)

#     updated_nlip = ollama_input.handle_follow_up_answer(
#         answer_nlip,
#         question_nlip,
#         system_desc,
#         validation_result,
#         conversation_token=conversation_token,
#         return_nlip=True,
#     )
#     updated_data = extract_response_content(updated_nlip)

#     out_dir = Path("./data/system-description/")
#     out_dir.mkdir(parents=True, exist_ok=True)
#     json_file_path = str(out_dir / f"{time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime())}-follow-up.json")

#     with open(json_file_path, "w", encoding="utf-8") as json_file:
#         json.dump(updated_data, json_file, indent=2)

#     schema_path = _project_root() / "data" / "schemas" / "system_description.schema.json"
#     results = validate_json(json_file_path, schema_path)

#     if len(results) == 0:
#         print_chat_message("System", "System Description JSON is Valid...", conversation_token=conversation_token)
#     else:
#         for result in results:
#             error_msg = NLIP_Factory.create_error_code(
#                 str(result),
#                 messagetype="Error",
#                 label="assistant",
#             )
#             error_msg.add_conversation_token(conversation_token, label="conversation")
#             print_chat_message("System", error_msg, conversation_token=conversation_token)
#         print_chat_message("System", "System Description JSON creation failed after follow-up.", conversation_token=conversation_token)

#     return json_file_path


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

    # TODO: Once validation is integrated, pipeline results should always include a status field.
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

        while ollama_input.nlip_to_text(user_response).strip().lower() != "no":
            follow_up_response = ollama_input.handle_follow_up_answer(user_response, question=question, system_desc=system_description_file, analysis_result=result, conversation_token=conversation_token)
            print_chat_message("System", follow_up_response, conversation_token=conversation_token)
            print_chat_message("System", "Do you have any other questions or clarifications?", conversation_token=conversation_token)
            user_response = ollama_input.get_user_response("Ask any questions/clarifications you have, or only type 'no' to end the conversation:", conversation_token=conversation_token)
        
        print_chat_message("System", "All files have been saved to the data folder and stress test analysis has completed, ending conversation...", conversation_token=conversation_token)