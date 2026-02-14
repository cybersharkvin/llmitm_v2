#!/usr/bin/env bash
set -euo pipefail
echo "=== Breaking ActionGraph: corrupting HTTP method on /api/Users steps ==="
docker exec llmitm_neo4j cypher-shell -u neo4j -p password \
    "MATCH (ag:ActionGraph)-[:HAS_STEP]->(s:Step)
     WHERE s.parameters CONTAINS '/api/Users'
     SET s.parameters = replace(s.parameters, '\"method\": \"GET\"', '\"method\": \"PATCH\"')
     SET s.command = replace(s.command, 'GET', 'PATCH')
     RETURN s.order, substring(s.command, 0, 80) AS command_preview"
echo "Steps corrupted (GET -> PATCH). Run 'make run' to trigger self-repair."
