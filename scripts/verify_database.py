#!/usr/bin/env python3
"""Verify the PostgreSQL knowledge vault and ingestion firewall."""

import subprocess
import sys

SQL = """
SELECT 'knowledge_vault_rows|' || COUNT(*) FROM knowledge_vault
UNION ALL
SELECT 'archived_sessions|' || COUNT(*) FROM archived_sessions
UNION ALL
SELECT 'rejected_sessions_in_vault|' || COUNT(*)
FROM knowledge_vault
WHERE session_id IN ('SES-103', 'SES-104')
UNION ALL
SELECT 'invalid_embedding_dimensions|' || COUNT(*)
FROM knowledge_vault
WHERE vector_dims(embedding) <> 1024
UNION ALL
SELECT 'framework_rows|' || COUNT(*)
FROM knowledge_vault WHERE stream_type = 'framework'
UNION ALL
SELECT 'voice_sample_rows|' || COUNT(*)
FROM knowledge_vault WHERE stream_type = 'voice_sample';
"""

def main():
    try:
        result = subprocess.run(
            [
                "docker", "exec", "-i", "rag-postgres",
                "sh", "-lc",
                'psql -X -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -F "|"'
            ],
            input=SQL,
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print("Database verification failed.")
        if getattr(exc, "stderr", None):
            print(exc.stderr)
        else:
            print(exc)
        return 1

    values = {}
    for line in result.stdout.splitlines():
        if "|" in line:
            key, value = line.split("|", 1)
            values[key] = int(value)

    for key, value in values.items():
        print(f"{key}: {value}")

    required = {
        "knowledge_vault_rows", "archived_sessions",
        "rejected_sessions_in_vault", "invalid_embedding_dimensions",
        "framework_rows", "voice_sample_rows",
    }

    if required - values.keys():
        print("FAIL: Missing database verification results.")
        return 1

    failures = []
    if values["knowledge_vault_rows"] == 0:
        failures.append("Knowledge vault is empty.")
    if values["rejected_sessions_in_vault"] != 0:
        failures.append("Rejected sessions found in knowledge vault.")
    if values["invalid_embedding_dimensions"] != 0:
        failures.append("Invalid embedding dimensions found.")
    if values["framework_rows"] == 0 or values["voice_sample_rows"] == 0:
        failures.append("One or both document streams are empty.")

    if failures:
        print("FAIL")
        for failure in failures:
            print("-", failure)
        return 1

    print("PASS: database and ingestion firewall checks succeeded.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
