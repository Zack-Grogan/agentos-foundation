"""Controlled ACP peer; no model, credentials or external tools."""

import json
import sys


def send(message):
    print(json.dumps({"jsonrpc": "2.0", **message}), flush=True)


pending_prompt = None
for line in sys.stdin:
    m = json.loads(line)
    method = m.get("method")
    if method == "initialize":
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
    elif method == "session/new":
        send({"id": m["id"], "result": {"sessionId": "fixture-session"}})
    elif method == "session/prompt":
        text = m["params"]["prompt"][0]["text"]
        if text == "malformed":
            print("not json", flush=True)
        elif text == "wait":
            pending_prompt = m["id"]
        else:
            pending_prompt = m["id"]
            send(
                {
                    "id": "permission-1",
                    "method": "session/request_permission",
                    "params": {
                        "sessionId": "fixture-session",
                        "options": [
                            {
                                "optionId": "native-allow",
                                "kind": "allow_once",
                                "name": "Allow",
                            }
                        ],
                    },
                }
            )
    elif m.get("id") == "permission-1":
        assert m["result"]["outcome"]["outcome"] == "cancelled"
        send(
            {
                "method": "session/update",
                "params": {
                    "sessionId": "fixture-session",
                    "update": {
                        "sessionUpdate": "agent_message_chunk",
                        "content": {
                            "type": "text",
                            "text": "Permission denied; fixture response.",
                        },
                    },
                },
            }
        )
        send({"id": pending_prompt, "result": {"stopReason": "end_turn"}})
    elif method == "session/cancel":
        send({"id": pending_prompt, "result": {"stopReason": "cancelled"}})
