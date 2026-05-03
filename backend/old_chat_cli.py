"""
Main user interface for the terminal chatbot (connect to nlip_web if time permits)
- handles conversation, follow-ups, and what-if scenarios
"""

from pathlib import Path
import json
import time
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

    missing_info = validation_result.get("needs_clarification", [])
    issues = validation_result.get("errors", [])

    prompt = f"""
    Given this system description:
    {system_desc}

    The validation step identified the following gaps:
    Needs Clarification: {missing_info}
    Issues: {issues}

    Generate ONE follow-up question to ask the user that would help fill in the missing information and/or address the issues. 
    The question should be clear and concise, and should directly relate to the gaps identified in the validation step.
    """

    question = ollama_input.ask_followup(prompt)
    print_chat_message("System", question)

    answer = input("Input your answer to the follow-up question:\n")

    updated_system_desc = ollama_input.handle_follow_up_answer(answer, question, system_desc, validation_result)

    out_dir = Path("./data/system-description/")
    out_dir.mkdir(parents=True, exist_ok=True)
    json_file_path = str(out_dir / (time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime()) + ".json"))

    # Write file
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=2)

    # Validate using schema
    schema_path = _project_root() / "data" / "schemas" / "system_description.schema.json"
    results = validate_json(json_file_path, schema_path)
    for result in results:
        print(result)
    if len(results) == 0:
        print("System Description JSON is Valid...\n")
    else:
        print("System Description JSON creation failed. Trying again...\n")

def chat_cli() -> None:
    """Main function to run the chat CLI."""
    print_chat_message("System", "Hi, I am your performance stress testing agent.")
    print_chat_message("System", "Please describe the system you want to analyze.")

    _, system_description_path = ollama_input.ask_sys_desc()
    system_description_file = Path(system_description_path).name

    print_chat_message("System", "Thank you for providing the system description. I will now analyze it and generate insights.")

    result = pipeline.pipeline(system_description_file)

    if result["status"] == "needs_clarification":
        print_chat_message("System", "I need some more information before I can continue.")
        print(result["context"])
    elif result["status"] == "error":
        print_chat_message("System", "I found an error when processing your system description:")
        print(result["errors"])
    else:
        print_chat_message("System", "Here are the insights I generated based on your system description:")
        print(result)
