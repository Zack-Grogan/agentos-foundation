"""ACP fixture that returns a valid plan and never contacts a model."""

import json
import sys


def send(value):
    print(json.dumps({"jsonrpc": "2.0", **value}), flush=True)


for line in sys.stdin:
    m = json.loads(line)
    if m.get("method") == "initialize":
        send(
            {
                "id": m["id"],
                "result": {
                    "protocolVersion": 1,
                    "agentCapabilities": {},
                    "authMethods": [],
                },
            }
        )
    elif m.get("method") == "session/new":
        send({"id": m["id"], "result": {"sessionId": "plan-session"}})
    elif m.get("method") == "session/prompt":
        plan = {
            "title": "ACP fixture plan",
            "objective": "A bounded example from a controlled peer.",
            "assumptions": ["Synthetic transport fixture."],
            "questions": ["Which source evidence is needed?"],
            "next_actions": ["Review the supplied evidence."],
        }
        send(
            {
                "method": "session/update",
                "params": {
                    "sessionId": "plan-session",
                    "update": {
                        "sessionUpdate": "agent_message_chunk",
                        "content": {"type": "text", "text": json.dumps(plan)},
                    },
                },
            }
        )
        send({"id": m["id"], "result": {"stopReason": "end_turn"}})
