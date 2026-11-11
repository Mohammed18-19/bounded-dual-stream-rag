import json
from pathlib import Path

INPUT_PATH = Path("data/mock_transcripts.json")
OUTPUT_PATH = Path("data/prepared_transcripts.json")


def sample_turns(turns: list[dict]) -> list[dict]:
    """Select the first 40 and last 20 turns without duplicate indices."""
    indices = list(range(min(40, len(turns))))

    if len(turns) > 40:
        indices.extend(range(max(40, len(turns) - 20), len(turns)))

    return [turns[i] for i in indices]


def validate_session(session: dict) -> None:
    required = {"id", "created_at", "title", "participants", "transcript"}

    missing = required - session.keys()
    if missing:
        raise ValueError(f"Session missing fields: {sorted(missing)}")

    if not session["participants"]:
        raise ValueError(f"{session['id']}: no participants")

    if not session["transcript"]:
        raise ValueError(f"{session['id']}: empty transcript")

    for participant in session["participants"]:
        if not {"name", "email", "is_team_member"} <= participant.keys():
            raise ValueError(f"{session['id']}: invalid participant")

    for turn in session["transcript"]:
        if not {"timestamp", "speaker", "text"} <= turn.keys():
            raise ValueError(f"{session['id']}: invalid transcript turn")

        if not turn["speaker"].strip() or not turn["text"].strip():
            raise ValueError(f"{session['id']}: empty speaker or text")


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(INPUT_PATH)

    sessions = json.loads(INPUT_PATH.read_text(encoding="utf-8"))

    if not isinstance(sessions, list) or not sessions:
        raise ValueError("Expected a non-empty JSON list of sessions")

    session_ids = [session.get("id") for session in sessions]

    if len(session_ids) != len(set(session_ids)):
        raise ValueError("Duplicate session IDs detected")

    prepared = []

    for session in sessions:
        validate_session(session)

        sampled = sample_turns(session["transcript"])

        prepared.append({
            "id": session["id"],
            "created_at": session["created_at"],
            "title": session["title"],
            "participants": session["participants"],
            "transcript": session["transcript"],
            "sampled_transcript": sampled,
            "sampling": {
                "original_turns": len(session["transcript"]),
                "sampled_turns": len(sampled),
            },
        })

    OUTPUT_PATH.write_text(
        json.dumps(prepared, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Validated sessions: {len(prepared)}")
    print(f"Total original turns: {sum(len(s['transcript']) for s in prepared)}")
    print(f"Total sampled turns: {sum(len(s['sampled_transcript']) for s in prepared)}")
    print(f"Output: {OUTPUT_PATH}")

    for session in prepared:
        print(
            f"{session['id']}: "
            f"{session['sampling']['original_turns']} original -> "
            f"{session['sampling']['sampled_turns']} sampled"
        )


if __name__ == "__main__":
    main()
