'''Validation of queue network conversions before sending to data generator'''

from typing import Any, Dict, List # for type hints

EXTERNAL_NODE_ID = "External"

def apply_defaults(model: Dict[str, Any], assumptions: List[str]) -> None:
    """Apply any default values to the model and record assumptions made."""
    queues = model.get("queues", [])

    if not queues:
        return
    
    # Infer entry point if missing
    entry_points = model.get("entry_points")
    if not entry_points:
        inferred_entry = queues[0]["id"]
        model["entry_points"] = inferred_entry
        assumptions.append(f"No entry point defined, assuming '{inferred_entry}' is the entry point.")

    # Check if exit queue (External) exists, and add if missing
    has_external = False
    for queue in queues:
        for next_queue in queue.get("next_queue", []):
            if next_queue.get("id") == EXTERNAL_NODE_ID:
                has_external = True
                break
    if not has_external:
        for queue in queues:
            if not queue.get("next_queue"):
                queue["next_queue"] = [{"id": EXTERNAL_NODE_ID, "probability": 100.0}]
                assumptions.append(f"Queue '{queue['id']}' had no outgoing edges, so an External exit was added.")
    
    # Apply default probabilities if missing (assume equal distribution)
    for queue in queues:
        next_queues = queue.get("next_queue", [])

        if not next_queues:
            continue

        has_missing_prob = any("probability" not in nq for nq in next_queues)
        total_prob = sum(nq.get("probability", 0) for nq in next_queues)
        if has_missing_prob or total_prob == 0:
            even_prob = 100.0 / len(next_queues)
            
            for next_queue in next_queues:
                next_queue["probability"] = even_prob
            
            assumptions.append(f"Queue '{queue['id']}' had missing or zero probabilities, so equal probabilities of {even_prob}% were assigned to each outgoing edge.")


def validate(model: Dict[str, Any]) -> List[str]:
    """Check logical rules and return a list of error messages. If the list is empty, the model is valid."""
    errors: List[str] = []

    queues = model.get("queues", [])

    queue_ids = [q["id"] for q in queues] # Collect queue IDs

    # Check if duplicate queue IDs exist
    if len(queue_ids) != len(set(queue_ids)):
        errors.append("Duplicate queue IDs found")

    # Check if entry queue IDs are valid
    entry_points = model.get("entry_points")
    if not entry_points:
        errors.append("No entry points defined")
    elif entry_points not in queue_ids:
        errors.append(f"Entry point '{entry_points}' does not match any queue ID")

    # Check if next_queues reference valid queue IDs
    for queue in queues:
        next_queues = queue.get("next_queue", [])
        for next_queue in next_queues:
            target_id = next_queue.get("id")
            if target_id not in queue_ids and target_id != EXTERNAL_NODE_ID:
                errors.append(f"Queue '{queue['id']}' points to unknown queue '{target_id}'.")

    # Check if exit queues (External) exists
    has_external = False
    for queue in queues:
        for next_queue in queue.get("next_queue", []):
            if next_queue.get("id") == EXTERNAL_NODE_ID:
                has_external = True
                break
    if not has_external:
        errors.append("No exit queue (External) defined in any next_queue.")

    # Check if probabilities sum to 100 for each queue
    for queue in queues:
        next_queues = queue.get("next_queue", [])
        if next_queues:
            total_prob = sum(next_queue.get("probability", 0) for next_queue in next_queues)
            if total_prob != 100:
                errors.append(f"Routing probabilities for queue '{queue['id']}' sum to {total_prob} instead of 100.")
        
    return errors

def enforce(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Finds a model, validates it, and returns a dictionary with the status, assumptions, and errors."""
    assumptions: List[str] = []
    
    try:
        model = get_model(doc)
    except Exception as e:
        return {"status": "error", "errors": [str(e)]}
    apply_defaults(model, assumptions)
    errors = validate(model)

    if errors:
        return {"status": "error", "errors": errors}
    
    return {"status": "ok", "model": doc, "assumptions": assumptions}


"""Helper Functions"""
def get_model(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Extract the queue network model from the JSON produced by converter."""
    if "system" not in doc:
        raise ValueError("JSON must contain a 'system' key")
    
    if not isinstance(doc["system"], dict):
        raise ValueError("'system' must be a dictionary")
    
    return doc["system"]