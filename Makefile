.PHONY: up down schema reset snapshot restore snapshot-baseline restore-baseline test run break-graph fix-graph seed

NAME ?= latest
PYTHON ?= .venv/bin/python3

up:
	docker compose up -d
	@echo "Waiting for Neo4j healthcheck..."
	@for i in $$(seq 1 30); do \
		docker exec llmitm_neo4j cypher-shell -u neo4j -p password "RETURN 1" >/dev/null 2>&1 && break; \
		sleep 2; \
	done
	@echo "Neo4j is ready."

down:
	docker compose down

schema:
	NEO4J_URI=bolt://localhost:7687 \
	NEO4J_USERNAME=neo4j \
	NEO4J_PASSWORD=password \
	NEO4J_DATABASE=neo4j \
	ANTHROPIC_API_KEY=dummy \
	TARGET_URL=http://localhost:3000 \
	$(PYTHON) -m llmitm_v2.repository.setup_schema

reset:
	./scripts/reset-graph.sh

snapshot:
	./scripts/export-snapshot.sh $(NAME)

restore:
	./scripts/restore-snapshot.sh $(NAME)

snapshot-baseline:
	$(MAKE) snapshot NAME=phase5-baseline

restore-baseline:
	$(MAKE) restore NAME=phase5-baseline

test:
	$(PYTHON) -m pytest tests/

run:
	$(PYTHON) -m llmitm_v2

break-graph:
	./scripts/break-graph.sh

fix-graph:
	./scripts/fix-graph.sh

seed:
	$(PYTHON) scripts/seed-demo-graph.py
