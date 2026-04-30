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

    Generate a follow-up question to ask the user that would help fill in the missing information or address the issues. 
    The question should be clear and concise, and should directly relate to the gaps identified in the validation step.
    """

    question = ollama_input.ask_followup(prompt)
    print_chat_message("System", question)

    answer = input("Input your answer to the follow-up question:\n")

    updated_system_desc = ollama_input.handle_follow_up_answer(answer, question, system_desc, validation_result)
    print_chat_message("System", "Thank you for your answer. I have updated the system description based on your input.")
    print_chat_message("System", f"Updated System Description: {updated_system_desc}")

def chat_cli() -> None:
    """Main function to run the chat CLI."""
    print_chat_message("System", "Hi, I am your performance stress testing agent.")
    print_chat_message("System", "Please describe the system you want to analyze.")

    _, system_description_path = ollama_input.ask_sys_desc()
    system_description_file = Path(system_description_path).name

    print_chat_message("System", "Thank you for providing the system description. I will now analyze it and generate insights.")

    result = pipeline.pipeline(system_description_file)
    print(result)