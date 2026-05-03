import os
import json
from datetime import datetime
from pathlib import Path
from jsonschema import Draft202012Validator
import backend.config as config


def validate_json(data_path, schema_path) -> list:
    """Validate a JSON file against a JSON Schema.
       Returns a list of error messages (empty if valid).
    """
    with open(schema_path) as f:
        schema = json.load(f)
    with open(data_path) as f:
        instance = json.load(f)

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)

    # Return readable list of messages
    return [f"at /{'/'.join(map(str, e.path))}: {e.message}" for e in errors]

def system_to_queue(system_path: str) -> str:
    """
    Convert a System Description JSON → Queueing Network JSON.
    Save output as queueing_network_{timestamp}.json inside queueing_network_dir.
    Returns absolute path to saved file.
    """
    # --- Load config ---
    cfg = config.get_config("dev_config.ini")
    qn_dir = Path(cfg.get("paths", "queueing_network_dir"))
    qn_dir.mkdir(parents=True, exist_ok=True)

    with open(system_path) as f:
        system_doc = json.load(f)

    comps = system_doc.get("system_description", [])

    # Collect all node IDs 
    defined_ids = {c["id"] for c in comps}
    referenced_ids = set()

    for c in comps:
        for e in c.get("edges", []):
            referenced_ids.add(e.get("to"))

    all_ids = defined_ids.union(referenced_ids)

    # Determine entry point
    incoming = {cid: 0 for cid in all_ids}
    for c in comps:
        for e in c.get("edges", []):
            incoming[e["to"]] = incoming.get(e["to"], 0) + 1

    entry_candidates = [cid for cid, x in incoming.items() if x == 0]
    entry_id = entry_candidates[0] if entry_candidates else (comps[0]["id"] if comps else "")

    # Convert components to queue structures
    comp_map = {c["id"]: c for c in comps}
    queues = []

    for qid in all_ids:
        c = comp_map.get(qid, {})  # empty if not defined

        next_queue = []
        edges = c.get("edges", [])

        if edges:
            for e in edges:
                try:
                    prob = float(e.get("weight", 0)) * 100.0
                except:
                    prob = 0.0

                next_queue.append({
                    "id": e.get("to", ""),
                    "probability": prob
                })
        else:
            # Terminal node -> goes to External
            next_queue.append({
                "id": "External",
                "probability": 100.0
            })

        queues.append({
            "id": qid,
            "service_rate": None,
            "next_queue": next_queue
        })

    result = {
        "system": {
            "lambda": None,
            "beta": None,
            "entry_points": entry_id,
            "constraint": {
                "service_rate_sum": 1.0
            },
            "queues": queues
        }
    }

    # --- Save file ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = qn_dir / f"queueing_network_{timestamp}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return str(out_path)

def queue_to_system(queue_path: str) -> str:
    """
    Convert a Queueing Network JSON → System Description JSON.
    Save output as system_description_{timestamp}.json inside system_description_dir.
    Returns absolute path to saved file.
    """
    # --- Load config ---
    cfg = config.get_config("dev_config.ini")
    sd_dir = Path(cfg.get("paths", "system_description_dir"))
    sd_dir.mkdir(parents=True, exist_ok=True)

    with open(queue_path) as f:
        queue_doc = json.load(f)

    qn = queue_doc.get("system", {})
    entry_id = qn.get("entry_points", "")
    queues = qn.get("queues", [])

    components = []
    for q in queues:
        cid = q.get("id", "")
        ctype = "connection" if cid == entry_id else "service"

        edges = []
        for nxt in q.get("next_queue", []):
            try:
                weight = float(nxt.get("probability", 0.0)) / 100.0
            except:
                weight = 0.0

            edges.append({
                "to": nxt.get("id", ""),
                "weight": weight,
                "num_msgs_per_sec": None
            })

        components.append({
            "id": cid,
            "type": ctype,
            "machine": "unknown",
            "description": "",
            "delay": None,
            "network_speed": None,
            "messages": [],
            "edges": edges
        })

    result = {
        "system_description": components,
        "metadata": []
    }

    # --- Save file ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = sd_dir / f"system_description_{timestamp}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return str(out_path)
