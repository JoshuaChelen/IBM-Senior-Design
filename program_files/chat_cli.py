"""
Main user interface for the terminal chatbot (connect to nlip_web if time permits)
- handles conversation, follow-ups, and what-if scenarios
"""

from pathlib import Path
from . import ollama_input, pipeline

def print_chat_message(speaker: str, message: str) -> None:
    """Prints a chat message to the terminal in a formatted way."""
    print(f"{speaker}: {message}")

def follow_up(system_desc: dict, validation_result: dict) -> None:
    """
    system_desc: original system description
    validation_result: output from validation step, expected to include
                       missing fields, gaps, or weaknesses
    """

    missing_info = validation_result.get("missing", [])
    issues = validation_result.get("issues", [])

    prompt = f"""
    Given this system description:
    {system_desc}

    The validation step identified the following gaps:
    Missing: {missing_info}
    Issues: {issues}

    Ask ONE concise follow-up question that would best help fill the most critical gap
    for performance stress testing.
    """

    question = ollama_input.ask_followup(prompt)
    print_chat_message("System", question)

def chat_cli() -> None:
    """Main function to run the chat CLI."""
    print_chat_message("System", "Hi, I am your performance stress testing agent.")
    print_chat_message("System", "Please describe the system you want to analyze.")

    _, system_description_path = ollama_input.ask_sys_desc()
    system_description_file = Path(system_description_path).name

    print_chat_message("System", "Thank you for providing the system description. I will now analyze it and generate insights.")

    result = pipeline.pipeline(system_description_file)
    print(result)