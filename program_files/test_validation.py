"""Wrote by CHATGPT for testing validation function"""
import json
from .validation import enforce

# Open a sample queueing network JSON file and validate it
with open("../data/queueing-network/queue_diverge_example.json") as f:
    doc = json.load(f)

result = enforce(doc)

print("STATUS:", result["status"])

if result["status"] == "ok":
    print("ASSUMPTIONS:", result["assumptions"])
else:
    print("ERRORS:", result["errors"])