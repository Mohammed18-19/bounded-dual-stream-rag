#!/usr/bin/env python3
"""Smoke-test the active Workflow B production webhook."""

import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

URL = os.getenv("RAG_URL", "http://localhost:5678/webhook/rag/query")
FALLBACK = "No documented coaching frameworks match this topic."

def ask(query):
    payload = json.dumps({"query": query}).encode()
    request = Request(
        URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode())

def main():
    try:
        unrelated = ask("What is the capital of France?")
        print("No-match:", json.dumps(unrelated, ensure_ascii=False))
        if unrelated.get("answer") != FALLBACK:
            raise AssertionError("Expected exact no-match fallback.")

        coaching = ask(
            "How can a manager reduce micromanagement while maintaining accountability?"
        )
        answer = coaching.get("answer", "")
        print("Coaching answer:", answer)
        if not isinstance(answer, str) or not answer.strip() or answer == FALLBACK:
            raise AssertionError("Expected a non-empty coaching answer.")

        print("PASS: both retrieval smoke tests succeeded.")
        return 0

    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, AssertionError) as exc:
        print("FAIL:", exc)
        print("Check that Workflow B is active and RAG_URL is correct.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
