from ollama import chat
from ollama import ChatResponse
import json
import time
import re
from .config import _project_root, get_config
from .data_conversion import validate_json
from pathlib import Path

def extract_json(response: str) -> str:
    sys_desc = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
    if not sys_desc:
        return None
    return sys_desc.group(1)

def ask_sys_desc():
    """
        Asks user for a system description and uses an Ollama model to translate 
        that description to JSON, fills in certain null values with config defaults,
        writes JSON to file and validates it, and returns the original model response. 
    """
    sys_desc_check = True
    while sys_desc_check:
        sys_desc = input("Input your system description (At least 10 words):\n")
        if len(sys_desc.split(" ")) > 9:
            sys_desc_check = False
        else:
            print("\nThe system description you inputted does not have enough information to be accurate. Please retype your system description and provide more information about it.\n")
    json_check = True
    loop_count = 0

    while json_check and loop_count < 5:
        print("\nGenerating system description JSON in data/system-description folder...\n")
        time.sleep(1)
        response: ChatResponse = chat(model="nlip-test-model", messages=[
            {
                'role': 'user',
                'content': sys_desc
            }
        ])
        clean_output = extract_json(response['message']['content'])
        parsed = json.loads(clean_output)

        if isinstance(parsed, list):
            data = {"system_description": parsed}
        elif isinstance(parsed, dict):
            if "system_description" in parsed and isinstance(parsed["system_description"], list):
                data = parsed
            elif parsed.get("id") is not None or parsed.get("edges") is not None:
                data = {"system_description": [parsed]}
            else:
                data = parsed
        else:
            data = {"system_description": []}

        # Get user-defined values for system and input them in generated JSON
        config = get_config("user_config.ini")
        comps = data.get("system_description") or []

        try:
            default_msg_size = config.getint('constraints', 'avg_message_size_bytes')
        except Exception:
            default_msg_size = None

        for comp in comps:
            if comp.get("network_speed") in (None, ""):
                try:
                    comp["network_speed"] = config.getint('test_system', 'network_bandwidth_mbps')
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
                    for m in msgs:
                        if isinstance(m, dict):
                            if m.get("message_size") in (None, ""):
                                m["message_size"] = default_msg_size
                    comp["messages"] = msgs
            else:
                comp["messages"] = {"message_size": default_msg_size} if default_msg_size is not None else {}

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
            json_check = False
        else:
            print("System Description JSON creation failed. Trying again...\n")
            loop_count += 1

    if (json_check):
        print("Exited due to too many retries of system description JSON creation...")
    return response, json_file_path