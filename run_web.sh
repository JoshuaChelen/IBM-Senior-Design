#!/bin/bash
cd "$(dirname "$0")"
VENV=$(poetry --directory nlip/nlip_web env info --path)
"$VENV/bin/python" nlip/nlip_web/nlip_web/stress_test_chat.py