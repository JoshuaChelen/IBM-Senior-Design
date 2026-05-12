# AI-Generated Code — Claude Sonnet 4.6 (Anthropic, claude.ai)
# Reviewed and tested by the development team.

"""
stress_test_chat.py

NLIP-based web server for the Performance Stress Testing Agent.
Subclasses SafeStatefulApplication and StatefulSession from nlip_server,
following the same pattern as text_chat.py.

Access at http://localhost:8030 after running run_web.bat / run_web.sh
"""

import sys
import logging
from pathlib import Path
from enum import Enum

# Add project root to path so backend/ is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from nlip_server import server
from nlip_sdk import nlip
from nlip_web import nlip_ext
from nlip_web.env import read_digits

logger = logging.getLogger("stress_test_chat")
logging.basicConfig(level=logging.INFO)


# ---------------------------------------------------------------------------
# Session states
# ---------------------------------------------------------------------------

class State(str, Enum):
    AWAITING_DESCRIPTION = "awaiting_description"  # waiting for user to describe their system
    AWAITING_FOLLOWUP    = "awaiting_followup"      # pipeline complete, accepting follow-up questions


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

class StressTestApplication(nlip_ext.SafeStatefulApplication):
    """
    NLIP application entry point. Creates and manages StressTestSession instances.
    Reads LOCAL_PORT from environment (default: 8030).
    """
    def __init__(self):
        super().__init__()
        self.local_port = read_digits("LOCAL_PORT", 8030)

    def create_stateful_session(self) -> server.NLIP_Session:
        """Creates a new session and initialises its state data."""
        session = StressTestSession()
        session.set_correlator()
        self.store_session_data(session.get_correlator(), {
            "state":                   State.AWAITING_DESCRIPTION,
            "result":                  None,   # stores analyzer JSON after pipeline runs
            "system_description_file": None,   # filename of generated system description JSON
        })
        return session


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

class StressTestSession(nlip_ext.StatefulSession):
    """
    Handles the two-turn conversation flow:
      Turn 1 — user provides system description -> pipeline runs -> results returned
      Turn 2+ — user asks follow-up questions -> LLM answers using analysis context
    """

    def execute(self, msg: nlip.NLIP_Message) -> nlip.NLIP_Message:
        from backend import ollama_input, pipeline as pipeline_module

        text = msg.extract_text()
        if not text:
            return nlip.NLIP_Factory.create_text("Please send a text message.")

        data = self.nlip_app.retrieve_session_data(self.get_correlator())
        if data is None:
            return nlip.NLIP_Factory.create_text("Error: session data not found.")

        state = data["state"]

        # ── Turn 1: system description -> run pipeline ────────────────────
        if state == State.AWAITING_DESCRIPTION:
            if len(text.split()) < 10:
                return nlip.NLIP_Factory.create_text(
                    "Please provide at least 10 words describing your system."
                )

            try:
                logger.info("Running pipeline for session %s...", self.get_correlator()[:8])

                # Convert natural language description to structured JSON via LLM
                _, sys_desc_path = ollama_input.ask_sys_desc(
                    user_message=text,
                    conversation_token=self.get_correlator(),
                )

                # Run the full analysis pipeline
                result = pipeline_module.pipeline(Path(sys_desc_path).name, show_plot=False)

                data["result"] = result
                data["system_description_file"] = Path(sys_desc_path).name

                status = result.get("status") if isinstance(result, dict) else None

                if status == "error":
                    data["state"] = State.AWAITING_DESCRIPTION
                    return nlip.NLIP_Factory.create_text(
                        "I found an error processing your system description. Please try again with more detail."
                    )

                data["state"] = State.AWAITING_FOLLOWUP

                # Return human-readable summary as text + full JSON as a structured submessage
                summary = _build_summary(result)
                response_msg = nlip.NLIP_Factory.create_text(summary)
                response_msg.add_json(result, label="analysis_result")
                return response_msg

            except Exception as e:
                logger.exception("Pipeline failed")
                data["state"] = State.AWAITING_DESCRIPTION
                return nlip.NLIP_Factory.create_text(f"Pipeline error: {str(e)}")

        # ── Turn 2+: follow-up questions ──────────────────────────────────
        elif state == State.AWAITING_FOLLOWUP:
            if text.strip().lower() == "no":
                data["state"] = State.AWAITING_DESCRIPTION
                return nlip.NLIP_Factory.create_text(
                    "Session ended. Feel free to describe another system whenever you're ready."
                )

            try:
                # Pass analysis result as context so LLM can answer accurately
                response_text = ollama_input.handle_follow_up_answer(
                    answer=text,
                    question="What would you like to know about the analysis?",
                    system_desc=data["system_description_file"],
                    analysis_result=data["result"],
                    conversation_token=self.get_correlator(),
                    return_nlip=False,
                )
                return nlip.NLIP_Factory.create_text(str(response_text))
            except Exception as e:
                logger.exception("Follow-up failed")
                return nlip.NLIP_Factory.create_text(f"Error: {str(e)}")

        return nlip.NLIP_Factory.create_text("Unexpected session state.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_summary(result: dict) -> str:
    """
    Converts analyzer JSON into a human-readable text summary displayed in the chat.
    Includes bottleneck, max safe lambda, baseline utilization bars, and what-if results.
    """
    if not isinstance(result, dict):
        return str(result)

    r = result.get("result", result)
    lines = ["Analysis complete!\n"]

    bottleneck = r.get("bottleneck")
    max_lambda  = r.get("max_lambda")

    if bottleneck:
        lines.append(f"Bottleneck:   {bottleneck}")
    if max_lambda is not None:
        lines.append(f"Max safe lambda:   {max_lambda:.4f}")

    baseline_utils = r.get("baseline", {}).get("utilizations", {})
    if baseline_utils:
        lines.append("\nBaseline utilization (rho):")
        for q, v in baseline_utils.items():
            filled = int(v * 20)
            bar = "█" * filled + "░" * (20 - filled)
            lines.append(f"  {q:20s} {bar} {v*100:.1f}%")

    what_if = r.get("what_if", {})
    if what_if:
        lines.append(f"\nWhat-if ({what_if.get('scenario', '')}):")
        for q, v in what_if.get("utilizations", {}).items():
            lines.append(f"  {q:20s} {v*100:.1f}%")

    lines += [
        "\nYou can ask follow-up questions, e.g.:",
        "  'What happens if traffic doubles?'",
        "  'Which component should I scale first?'",
        "  Type 'no' to end the session.",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    STATIC_DIR = str(Path(__file__).resolve().parent.parent / "static")
    app_instance = StressTestApplication()
    webapp = nlip_ext.WebApplication(
        indexFile=str(Path(__file__).resolve().parent.parent / "static" / "stress_test.html"),
        favicon_path=str(Path(__file__).resolve().parent.parent / "static" / "NLIPlogo.png"),
        static_dir=STATIC_DIR,
    )
    app = webapp.setup_webserver(app_instance, port=app_instance.local_port)