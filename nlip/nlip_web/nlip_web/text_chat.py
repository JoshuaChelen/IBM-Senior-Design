import json
import re
import sys
import os
import time
from pathlib import Path
from nlip_web.genai import StatefulGenAI
from nlip_web import nlip_ext as nlip_ext
from nlip_web.env import read_digits, read_string
from nlip_server import server
from nlip_sdk import nlip

# Add project root to path so we can import validation
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from program_files.validation import enforce
from program_files.data_conversion import system_to_queue, validate_json
from program_files.config import _project_root

def extract_json(response: str):
    """Extract JSON from AI response if present."""
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None
    return None

class ChatApplication(nlip_ext.SafeStatefulApplication):
    def __init__(self):
        super().__init__()
        self.local_port = read_digits("LOCAL_PORT", 8010)
        self.model = read_string("CHAT_MODEL", "nlip-test-model")
        self.host = read_string("CHAT_HOST", "localhost")
        self.port = read_digits("CHAT_PORT", 11434)

    def create_stateful_session(self) -> server.NLIP_Session:
        genAI = StatefulGenAI(self.host, self.port, self.model)
        session = ChatSession()
        session.set_correlator()
        self.store_session_data(session.get_correlator(), genAI)
        return session


class ChatSession(nlip_ext.StatefulSession):

    def execute(self, msg: nlip.NLIP_Message) -> nlip.NLIP_Message:
        text = msg.extract_text()
        chat_server = self.nlip_app.retrieve_session_data(self.get_correlator())
        if chat_server is None:
            return nlip.NLIP_Factory.create_text("Error: Can't find my chat server")

        response = chat_server.chat(text)

        # Try to extract and validate queue network JSON from AI response
        parsed = extract_json(response)
        if parsed is not None:
            # Normalize into system_description shape
            if isinstance(parsed, list):
                system_doc = {"system_description": parsed}
            elif isinstance(parsed, dict):
                if "system_description" in parsed:
                    system_doc = parsed
                elif parsed.get("id") is not None or parsed.get("edges") is not None:
                    system_doc = {"system_description": [parsed]}
                else:
                    system_doc = parsed
            else:
                system_doc = {"system_description": []}

            # Write temporary system description file
            tmp_dir = Path(_project_root() / "./data/system-description")
            tmp_dir.mkdir(parents=True, exist_ok=True)
            json_file_path = str(tmp_dir / (time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime()) + ".json"))

            with open(json_file_path, "w", encoding="utf-8") as json_file:
                json.dump(system_doc, json_file, indent=2)
            
            schema_path = _project_root() / "data" / "schemas" / "system_description.schema.json"
            result = validate_json(json_file_path, schema_path)

            if result:
                validation_msg = "\n\n❌ System description is invalid:\n" + "\n".join(f"- {e}" for e in result)
                return nlip.NLIP_Factory.create_text(response + validation_msg)

            # Convert system description -> queue network
            queue_path = system_to_queue(str(json_file_path))

            # Load converted queue network and validate it
            with open(queue_path, "r", encoding="utf-8") as f:
                queue_doc = json.load(f)
                    
            result = enforce(queue_doc)

            if result["status"] == "ok":
                assumptions = result.get("assumptions", [])
                validation_msg = "\n\n✅ Queue network is valid!"
                if assumptions:
                    validation_msg += "\n⚠️ Assumptions made:\n" + "\n".join(f"- {a}" for a in assumptions)
                return nlip.NLIP_Factory.create_text(response + validation_msg)
            else:
                errors = result.get("errors", [])
                error_msg = "\n\n❌ Validation failed:\n" + "\n".join(f"- {e}" for e in errors)
                return nlip.NLIP_Factory.create_text(response + error_msg)

        # No JSON found, just return AI response as normal
        return nlip.NLIP_Factory.create_text(response)


if __name__ == "__main__":
    chatapp = ChatApplication()
    webapp = nlip_ext.WebApplication(indexFile="static/text_chat.html")
    app = webapp.setup_webserver(chatapp, port=chatapp.local_port)