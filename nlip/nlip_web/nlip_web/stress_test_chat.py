"""
stress_test_chat.py

NLIP-based server for the Performance Stress Testing Agent.
Mirrors the structure of text_chat.py exactly, using nlip_sdk + nlip_server.

Place at: E:/UD/498/IBM-Senior-Design/nlip/nlip_web/nlip_web/stress_test_chat.py

Run with:
    $env:CHAT_MODEL = "granite3-moe"
    poetry run python nlip_web/stress_test_chat.py
    # Access at http://localhost:8030
"""

import sys
import json
import logging
import os
from pathlib import Path
from enum import Enum

# ---------------------------------------------------------------------------
# Path setup — make program_files importable from the project root
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
# nlip/nlip_web/nlip_web/stress_test_chat.py  →  4 parents up = IBM-Senior-Design
sys.path.insert(0, str(PROJECT_ROOT))

from nlip_server import server
from nlip_sdk import nlip
from nlip_web import nlip_ext
from nlip_web.env import read_digits, read_string

logger = logging.getLogger("stress_test_chat")
logging.basicConfig(level=logging.INFO)


# ---------------------------------------------------------------------------
# Session state enum
# ---------------------------------------------------------------------------

class SessionState(str, Enum):
    AWAITING_DESCRIPTION = "awaiting_description"
    AWAITING_FOLLOWUP    = "awaiting_followup"


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

class StressTestApplication(nlip_ext.SafeStatefulApplication):
    def __init__(self):
        super().__init__()
        self.local_port = read_digits("LOCAL_PORT", 8030)
        self.model      = read_string("CHAT_MODEL", "granite3-moe")
        self.host       = read_string("CHAT_HOST",  "localhost")
        self.port       = read_digits("CHAT_PORT",  11434)

    def create_stateful_session(self) -> server.NLIP_Session:
        session = StressTestSession()
        session.set_correlator()
        # Store per-session state dict
        self.store_session_data(session.get_correlator(), {
            "state":   SessionState.AWAITING_DESCRIPTION,
            "result":  None,   # analyzer JSON once pipeline finishes
            "history": [],     # LLM conversation history for follow-ups
            "model":   self.model,
            "host":    self.host,
            "port":    self.port,
        })
        return session


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

class StressTestSession(nlip_ext.StatefulSession):

    def execute(self, msg: nlip.NLIP_Message) -> nlip.NLIP_Message:
        text = msg.extract_text()
        if not text:
            return nlip.NLIP_Factory.create_text("Please send a text message.")

        data = self.nlip_app.retrieve_session_data(self.get_correlator())
        if data is None:
            return nlip.NLIP_Factory.create_text("Error: session data not found.")

        state = data["state"]

        # ── State 1: waiting for system description ──────────────────────
        if state == SessionState.AWAITING_DESCRIPTION:
            if len(text.split()) < 10:
                return nlip.NLIP_Factory.create_text(
                    "Please provide at least 10 words describing your system."
                )

            try:
                logger.info("Running pipeline for session %s…", self.get_correlator()[:8])

                # Import here to avoid circular imports at module load time
                from program_files import ollama_input, pipeline as pipeline_module

                _, sys_desc_path = ollama_input.ask_sys_desc_from_text(text)
                result = pipeline_module.pipeline(Path(sys_desc_path).name)

                data["result"] = result
                data["state"]  = SessionState.AWAITING_FOLLOWUP

                # Build response: summary text + structured JSON submessage
                summary = _build_summary(result)
                response_msg = nlip.NLIP_Factory.create_text(summary)
                response_msg.addJson(result, label="analysis_result")
                return response_msg

            except Exception as e:
                logger.exception("Pipeline failed")
                return nlip.NLIP_Factory.create_text(f"Pipeline error: {str(e)}")

        # ── State 2: follow-up questions ─────────────────────────────────
        elif state == SessionState.AWAITING_FOLLOWUP:
            try:
                answer = _ask_followup(
                    model=data["model"],
                    result=data["result"],
                    history=data["history"],
                    user_question=text,
                )
                return nlip.NLIP_Factory.create_text(answer)
            except Exception as e:
                logger.exception("Follow-up failed")
                return nlip.NLIP_Factory.create_text(f"Error: {str(e)}")

        return nlip.NLIP_Factory.create_text("Unexpected session state.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_summary(result: dict) -> str:
    """Convert analyzer JSON into a readable text summary."""
    r = result.get("result", {})
    lines = [
        "✓ Analysis complete!\n",
        f"Bottleneck:    {r.get('bottleneck', 'N/A')}",
        f"Max safe λ:    {r.get('max_lambda', 0):.4f}",
        "",
        "Baseline utilization (ρ):",
    ]
    for q, v in (r.get("baseline", {}).get("utilizations", {}) or {}).items():
        bar = "█" * int(v * 20) + "░" * (20 - int(v * 20))
        lines.append(f"  {q:20s} {bar} {v*100:.1f}%")

    lines += [
        "",
        f"What-if ({r.get('what_if', {}).get('scenario', '')})",
    ]
    for q, v in (r.get("what_if", {}).get("utilizations", {}) or {}).items():
        lines.append(f"  {q:20s} {v*100:.1f}%")

    lines += [
        "",
        "You can now ask follow-up questions, e.g.:",
        "  'What happens if traffic doubles?'",
        "  'Which component should I scale first?'",
    ]
    return "\n".join(lines)


def _ask_followup(model: str, result: dict, history: list, user_question: str) -> str:
    """Send a follow-up question to Ollama with analysis context."""
    from ollama import chat as ollama_chat

    system_prompt = (
        "You are a performance stress testing expert. "
        "The user has already run a queueing-theory analysis. Results:\n\n"
        f"{json.dumps(result, indent=2)}\n\n"
        "Answer what-if questions concisely, referencing specific numbers."
    )

    messages = [{"role": "system", "content": system_prompt}]
    messages += history
    messages.append({"role": "user", "content": user_question})

    response = ollama_chat(model=model, messages=messages)
    reply = response["message"]["content"]

    history.append({"role": "user",      "content": user_question})
    history.append({"role": "assistant", "content": reply})

    return reply


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app_instance = StressTestApplication()
    webapp = nlip_ext.WebApplication(indexFile="static/stress_test.html")
    app = webapp.setup_webserver(app_instance, port=app_instance.local_port)