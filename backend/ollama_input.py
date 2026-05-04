from __future__ import annotations
import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any, Optional, Union
from urllib.error import URLError
from urllib.request import Request, urlopen
from ollama import ChatResponse, chat
from .config import _project_root, get_config
from .data_conversion import validate_json
from nlip.nlip_sdk.nlip_sdk.nlip import NLIP_Factory, NLIP_Message

DEFAULT_LANGUAGE = "english"
DEFAULT_MODEL = "nlip-test-model"
# DEFAULT_NLIP_ENDPOINT = "http://127.0.0.1:8000/nlip"

def new_conversation_token(prefix: str = "stress-test-cli") -> str:
    """Create an opaque NLIP conversation token for one CLI session."""
    return f"{prefix}-{uuid.uuid4()}"

def text_to_nlip(message: Union[NLIP_Message, dict[str, Any], str]) -> NLIP_Message:
    """Convert given input into NLIP message."""
    if isinstance(message, NLIP_Message):
        return message
    if isinstance(message, str):
        message = json.loads(message)
    return NLIP_Message.model_validate(message)

def nlip_to_text(message: Union[NLIP_Message, dict[str, Any], str, Any]) -> str:
    """Get just message content from an NLIP message."""
    if isinstance(message, dict) and not {"format", "Format"}.intersection(message.keys()):
        return json.dumps(message, indent=2)

    if isinstance(message, NLIP_Message) or isinstance(message, dict):
        try:
            msg = text_to_nlip(message)
        except Exception:
            return json.dumps(message, indent=2) if isinstance(message, dict) else str(message)

        text = msg.extract_text(DEFAULT_LANGUAGE) or msg.extract_text(None)
        if text is not None:
            return text
        if str(getattr(msg.format, "value", msg.format)).lower() == "structured":
            return json.dumps(msg.content, indent=2)
        return str(msg.content)
    return str(message)

def print_nlip_message(speaker: str, message: Union[NLIP_Message, str, dict[str, Any]]) -> NLIP_Message:
    """Convert message into NLIP format in case it isn't already, print it to terminal, and return it."""
    if isinstance(message, NLIP_Message):
        msg = message
    elif isinstance(message, dict):
        msg = NLIP_Factory.create_json(message, messagetype="Response", label=speaker.lower())
    else:
        msg = NLIP_Factory.create_text(str(message), label=speaker.lower())

    print(f"{speaker}: {nlip_to_text(msg)}")
    return msg

def get_user_response(prompt: str, *, conversation_token: Optional[str] = None, label: str = "user") -> NLIP_Message:
    """Prompt the user for a response and return it as an NLIP message."""
    prompt_msg = NLIP_Factory.create_text(
        prompt,
        language=DEFAULT_LANGUAGE,
        messagetype="Request",
        label="assistant",
    )
    if conversation_token:
        prompt_msg.add_conversation_token(conversation_token, label="conversation")

    user_reply = input(f"{nlip_to_text(prompt_msg)}\n")
    user_msg = NLIP_Factory.create_text(
        user_reply,
        language=DEFAULT_LANGUAGE,
        messagetype="Request",
        label=label,
    )
    if conversation_token:
        user_msg.add_conversation_token(conversation_token, label="conversation")

    return user_msg

def copy_token_submessages(source: NLIP_Message, target: NLIP_Message) -> None:
    """Copy token submessages from one NLIP message to another for conversation tracking."""
    for submsg in getattr(source, "submessages", None) or []:
        if str(getattr(submsg.format, "value", submsg.format)).lower() == "token":
            target.add_submessage(submsg)

def post_nlip_message(endpoint: str, request_message: NLIP_Message, *, timeout: int = 60) -> NLIP_Message:
    """Send NLIP message to NLIP server endpoint."""
    body = json.dumps(request_message.to_dict()).encode("utf-8")
    request = Request(
        endpoint,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            post = response.read().decode("utf-8")
    except URLError as exc:
        error_msg = NLIP_Factory.create_error_code(
            f"NLIP server request failed: {exc}",
            messagetype="Error",
            label="assistant",
        )
        conversation_token = request_message.extract_conversation_token()
        if conversation_token:
            error_msg.add_conversation_token(conversation_token, label="conversation")
        return error_msg
    return text_to_nlip(post)

def local_ollama_response(request_message: NLIP_Message, *, model: str = DEFAULT_MODEL) -> NLIP_Message:
    """Generate response from local Ollama model and convert to NLIP format."""
    prompt = nlip_to_text(request_message)
    response: ChatResponse = chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )

    response_message = NLIP_Factory.create_text(
        response["message"]["content"],
        language=DEFAULT_LANGUAGE,
        label="assistant",
        messagetype="Response",
    )
    copy_token_submessages(request_message, response_message)
    return response_message

def send_message(request_message: Union[NLIP_Message, dict[str, Any], str], *, model: str = DEFAULT_MODEL) -> NLIP_Message:
    """Send an NLIP request either to NLIP server or local Ollama model."""
    nlip_request = text_to_nlip(request_message)

    endpoint = os.getenv("NLIP_SERVER_URL", "").strip()
    if endpoint:
        nlip_response = post_nlip_message(endpoint, nlip_request)
    else:
        nlip_response = local_ollama_response(nlip_request, model=model)

    return nlip_response

def extract_json(response: str) -> Optional[str]:
    """Extract JSON object from LLM response (used to extract system description)."""
    if not response:
        return None

    search = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", response, re.IGNORECASE)
    found = search.group(1) if search else response
    json_object = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", found)
    return json_object.group(1).strip() if json_object else None

def shape_sys_desc(parsed: Any) -> dict[str, Any]:
    """Format model JSON into the defined system description schema if needed."""
    if isinstance(parsed, list):
        return {"system_description": parsed}
    if isinstance(parsed, dict):
        if "system_description" in parsed and isinstance(parsed["system_description"], list):
            return parsed
        if parsed.get("id") is not None or parsed.get("edges") is not None or parsed.get("machine") is not None:
            return {"system_description": [parsed]}
        return parsed
    return {"system_description": []}

def apply_config_defaults(data: dict[str, Any]) -> dict[str, Any]:
    """Fill unknown values in system description JSON with defaults from config where possible."""
    config = get_config("user_config.ini")
    comps = data.get("system_description") or []

    default_msg_size = config.getint("constraints", "avg_message_size_bytes")

    for comp in comps:
        if not isinstance(comp, dict):
            continue

        if comp.get("network_speed") in (None, ""):
            try:
                comp["network_speed"] = config.getint("test_system", "network_bandwidth_mbps")
            except Exception:
                comp["network_speed"] = None

        msgs = comp.get("messages")
        if isinstance(msgs, dict):
            if msgs.get("message_size") in (None, ""):
                msgs["message_size"] = default_msg_size
            comp["messages"] = msgs
        elif isinstance(msgs, list):
            if not msgs:
                comp["messages"] = [{"message_size": default_msg_size}] if default_msg_size is not None else []
            else:
                for msg in msgs:
                    if isinstance(msg, dict) and msg.get("message_size") in (None, ""):
                        m["message_size"] = default_msg_size
                comp["messages"] = msgs
        else:
            comp["messages"] = {"message_size": default_msg_size} if default_msg_size is not None else {}

    return data


def write_sys_desc_file(data: dict[str, Any], *, attempt: int = 0) -> str:
    """Write system description JSON to file and return file path."""
    out_dir = Path("./data/system-description/")
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime())}-{attempt}.json"
    json_file_path = str(out_dir / filename)
    with open(json_file_path, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=2)
    return json_file_path

def validation_feedback(results: list[Any], raw_response: str) -> str:
    """Return validation feedback to user based on schema validation results."""
    errors = "\n".join(str(result) for result in results) or "No schema errors were returned."
    return (
        "The previous generated JSON did not validate. Fix these exact schema errors and regenerate only valid JSON.\n"
        f"Schema errors:\n{errors}\n\n"
        f"Previous model response:\n{raw_response[:4000]}"
    )

def validation_fail_response(system_description: str, validation_feedback: Optional[str]) -> str:
    """Prompt for ollama to generate system description JSON in the event of validation errors."""
    if not validation_feedback:
        return system_description
    return (
        f"Original system description:\n{system_description}\n\n"
        f"Validation feedback from the previous NLIP response:\n{validation_feedback}\n\n"
        "Regenerate the complete system description JSON. Return only JSON."
    )

def ask_sys_desc(user_message: Optional[Union[NLIP_Message, dict[str, Any], str]] = None, *, conversation_token: Optional[str] = None) -> tuple[NLIP_Message, str]:
    """
    Ask for a system description via NLIP, generate JSON via an NLIP exchange,
    validate it, and return (last NLIP model response, JSON file path).
    """
    conversation_token = conversation_token or new_conversation_token()

    if user_message is None:
        while True:
            user_nlip = get_user_response(
                "Input your system description (At least 10 words):",
                conversation_token=conversation_token,
            )
            sys_desc = nlip_to_text(user_nlip).strip()
            if len(sys_desc.split()) > 9:
                break

            short_desc_msg = NLIP_Factory.create_text(
                "The system description you inputted does not have enough information to be accurate. "
                "Please retype your system description and provide more information about it.",
                language=DEFAULT_LANGUAGE,
                messagetype="Response",
                label="assistant",
            )
            short_desc_msg.add_conversation_token(conversation_token, label="conversation")
            print_nlip_message("System", short_desc_msg)
    else:
        if isinstance(user_message, str):
            user_nlip = NLIP_Factory.create_text(
                user_message,
                language=DEFAULT_LANGUAGE,
                messagetype="Request",
                label="user",
            )
            user_nlip.add_conversation_token(conversation_token, label="conversation")
        else:
            user_nlip = text_to_nlip(user_message)
        sys_desc = nlip_to_text(user_nlip).strip()

    json_check = True
    loop_count = 0
    last_response = NLIP_Factory.create_text(
        "",
        language=DEFAULT_LANGUAGE,
        messagetype="Response",
        label="assistant",
    )
    last_response.add_conversation_token(conversation_token, label="conversation")
    last_json_file_path: Optional[str] = None
    feedback: Optional[str] = None

    while json_check and loop_count < 5:
        status_msg = NLIP_Factory.create_text(
            "Generating system description JSON in data/system-description folder...",
            language=DEFAULT_LANGUAGE,
            messagetype="Response",
            label="assistant",
        )
        status_msg.add_conversation_token(conversation_token, label="conversation")
        print_nlip_message("System", status_msg)
        time.sleep(1)

        generation_prompt = validation_fail_response(sys_desc, feedback)
        request_nlip = NLIP_Factory.create_text(
            generation_prompt,
            language=DEFAULT_LANGUAGE,
            messagetype="Request",
            label="user",
        )
        request_nlip.add_conversation_token(conversation_token, label="conversation")
        if feedback:
            request_nlip.add_text(feedback, language=DEFAULT_LANGUAGE, label="validation_feedback")

        last_response = send_message(request_nlip)
        raw_response = nlip_to_text(last_response)
        clean_output = extract_json(raw_response)

        if clean_output is None:
            feedback = "The model response did not contain a JSON object or array. Return only valid JSON."
            error_msg = NLIP_Factory.create_error_code(
                "System Description JSON creation failed. Trying again with JSON extraction feedback.",
                messagetype="Error",
                label="assistant",
            )
            error_msg.add_conversation_token(conversation_token, label="conversation")
            print_nlip_message("System", error_msg)
            loop_count += 1
            continue

        try:
            parsed = json.loads(clean_output)
        except json.JSONDecodeError as exc:
            feedback = f"The model response contained invalid JSON: {exc}. Return only valid JSON."
            error_msg = NLIP_Factory.create_error_code(
                "System Description JSON creation failed. Trying again with JSON parse feedback.",
                messagetype="Error",
                label="assistant",
            )
            error_msg.add_conversation_token(conversation_token, label="conversation")
            print_nlip_message("System", error_msg)
            loop_count += 1
            continue

        data = apply_config_defaults(shape_sys_desc(parsed))
        last_json_file_path = write_sys_desc_file(data, attempt=loop_count)

        schema_path = _project_root() / "data" / "schemas" / "system_description.schema.json"
        results = validate_json(last_json_file_path, schema_path)

        if len(results) == 0:
            valid_msg = NLIP_Factory.create_text(
                "System Description JSON is Valid...",
                language=DEFAULT_LANGUAGE,
                messagetype="Response",
                label="assistant",
            )
            valid_msg.add_conversation_token(conversation_token, label="conversation")
            print_nlip_message("System", valid_msg)
            json_check = False
        else:
            for result in results:
                error_msg = NLIP_Factory.create_error_code(
                    str(result),
                    messagetype="Error",
                    label="assistant",
                )
                error_msg.add_conversation_token(conversation_token, label="conversation")
                print_nlip_message("System", error_msg)
            feedback = validation_feedback(results, raw_response)

            retry_msg = NLIP_Factory.create_text(
                "System Description JSON creation failed. Trying again with validation feedback...",
                language=DEFAULT_LANGUAGE,
                messagetype="Response",
                label="assistant",
            )
            retry_msg.add_conversation_token(conversation_token, label="conversation")
            print_nlip_message("System", retry_msg)
            loop_count += 1

    if json_check:
        error_message = "Exited due to too many retries of system description JSON creation."
        error_msg = NLIP_Factory.create_error_code(
            error_message,
            messagetype="Error",
            label="assistant",
        )
        error_msg.add_conversation_token(conversation_token, label="conversation")
        print_nlip_message("System", error_msg)
        if last_json_file_path is None:
            raise RuntimeError(error_message)

    return last_response, last_json_file_path or ""

def ask_follow_up(prompt: Union[str, NLIP_Message, dict[str, Any]], *, conversation_token: Optional[str] = None, return_nlip: bool = False) -> Union[str, NLIP_Message]:
    """Ask Ollama a follow-up prompt through an NLIP request/response exchange."""
    if isinstance(prompt, NLIP_Message):
        request_nlip = prompt
    else:
        request_nlip = NLIP_Factory.create_text(
            nlip_to_text(prompt),
            language=DEFAULT_LANGUAGE,
            messagetype="Request",
            label="user",
        )
        if conversation_token:
            request_nlip.add_conversation_token(conversation_token, label="conversation")

    response_nlip = send_message(request_nlip)
    return response_nlip if return_nlip else nlip_to_text(response_nlip)

def handle_follow_up_answer(answer: Union[str, NLIP_Message, dict[str, Any]], question: Union[str, NLIP_Message, dict[str, Any]], system_desc: dict[str, Any], validation_result: dict[str, Any], *, conversation_token: Optional[str] = None, return_nlip: bool = False) -> Union[str, NLIP_Message]:
    """Generate an updated system description based on the user's answer to the follow-up question."""
    answer_text = nlip_to_text(answer)
    question_text = nlip_to_text(question)

    prompt = (
        f"System Description: {system_desc}\n"
        f"Validation Result: {validation_result}\n"
        f"Follow-up Question: {question_text}\n"
        f"Follow-up Answer: {answer_text}\n\n"
        "Based on the original system description, the validation results, and the user's answer to the "
        "follow-up question, update the system description or validation results as needed. If the user's "
        "answer provides new information that fills in missing details or addresses issues identified in the "
        "validation step, incorporate that information into an updated system description or validation result. "
        "If the user's answer does not provide new information or does not address the gaps identified in the "
        "validation step, indicate that no updates are necessary. Return the updated result as JSON when possible."
    )

    request_nlip = NLIP_Factory.create_text(
        prompt,
        language=DEFAULT_LANGUAGE,
        messagetype="Request",
        label="user",
    )
    if conversation_token:
        request_nlip.add_conversation_token(conversation_token, label="conversation")

    response_nlip = send_message(request_nlip)
    return response_nlip if return_nlip else nlip_to_text(response_nlip)
