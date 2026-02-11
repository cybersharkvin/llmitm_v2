# Neo4j Backup, Restore & Snapshot Strategies

## Overview

This guide covers backup/restore strategies for Neo4j Community Edition in our Docker Compose setup. Community Edition lacks online backup (`neo4j-admin backup`), so we use offline dump/load plus APOC Cypher export.

## Methods

### 1. Binary Dump/Load (`neo4j-admin database dump/load`)

**Best for**: Fast, complete snapshots including indexes and constraints.

**Trade-offs**:
- Requires Neo4j to be **stopped** (Community Edition limitation)
- Binary format — not human-readable, not diffable
- Version-coupled: dump from Neo4j 5.x must be loaded into 5.x

**Commands (our Docker setup)**:

```bash
# Dump (Neo4j must be stopped)
docker run --rm \
    -v <volume>:/data \
    -v ./backups:/backups \
    neo4j/neo4j-admin:5-community \
    neo4j-admin database dump neo4j --to-path=/backups --overwrite-destination=true

# Load (Neo4j must be stopped)
docker run --rm \
    -v <volume>:/data \
    -v ./backups:/backups \
    neo4j/neo4j-admin:5-community \
    neo4j-admin database load neo4j --from-path=/backups --overwrite-destination=true
```

**Key detail**: The `neo4j/neo4j-admin:5-community` image version must match the running Neo4j version.

### 2. APOC Cypher Export (`apoc.export.cypher.all`)

**Best for**: Human-readable, git-trackable snapshots. Diffable across versions.

**Trade-offs**:
- Slower than binary for large databases
- Does not capture indexes/constraints (we strip them; `setup_schema.py` is source of truth)
- Requires APOC plugin + file export enabled

**Docker Compose config required**:
```yaml
environment:
  NEO4J_apoc_export_file_enabled: "true"
  NEO4J_apoc_import_file_enabled: "true"
  NEO4J_apoc_import_file_use__neo4j__config: "true"
volumes:
  - ./snapshots:/var/lib/neo4j/import/snapshots
```

**Command**:
```cypher
CALL apoc.export.cypher.all('/import/snapshots/name.cypher', {format: 'cypher-shell'})
```

### 3. Cypher `MATCH (n) DETACH DELETE n` (Online Reset)

**Best for**: Quick wipe without restart. Development/testing only.

**Trade-offs**:
- Does not remove constraints/indexes (use `apoc.schema.assert({}, {})` for that)
- Not suitable for large databases (memory pressure)

## Our Approach: Dual Strategy

| Artifact | Format | Location | Git-tracked | Purpose |
|----------|--------|----------|-------------|---------|
| Binary dump | `.dump` | `backups/` | No (gitignored) | Fast restore for demo resets |
| Cypher export | `.cypher` | `snapshots/` | Yes (diffable) | Audit trail, code review |

**Schema is always separate**: `setup_schema.py` is the single source of truth. Cypher exports have schema lines stripped. Restore always runs `setup_schema.py` after loading data.

## Gotchas

1. **Volume name detection**: Docker Compose prefixes volume names with the project directory. Use `docker volume ls --filter name=neo4j_data -q` to detect dynamically.
2. **Healthcheck after restart**: Neo4j takes several seconds to start. Always poll `cypher-shell "RETURN 1"` before running queries.
3. **neo4j-admin image**: Must match the running Neo4j major version (both `5-community`).
4. **APOC file paths**: Exports go to Neo4j's import directory. The bind mount maps `./snapshots` to `/var/lib/neo4j/import/snapshots`.
5. **dump file naming**: `neo4j-admin database dump` produces `neo4j.dump` (named after the database). Scripts rename to `<name>.dump`.

## Makefile Targets

```
make snapshot NAME=x    # Binary dump + Cypher export
make restore NAME=x     # Binary load + schema apply
make reset              # Online wipe + schema recreate
make snapshot-baseline  # Shortcut: NAME=phase5-baseline
make restore-baseline   # Shortcut: NAME=phase5-baseline
```
