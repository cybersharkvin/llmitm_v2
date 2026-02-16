"""WSGI entry point for gunicorn — replaces Flask dev server for real-time SSE."""

import logging
import os

from neo4j import GraphDatabase

from llmitm_v2.config import Settings
from llmitm_v2.debug_logger import set_event_callback
from llmitm_v2.monitor.server import _push_event, app
from llmitm_v2.repository import GraphRepository
from llmitm_v2.repository.setup_schema import setup_schema

logging.basicConfig(level=logging.INFO)
logging.getLogger("neo4j").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("anthropic").setLevel(logging.WARNING)

settings = Settings()

driver = GraphDatabase.driver(
    settings.neo4j_uri,
    auth=(settings.neo4j_username, settings.neo4j_password),
)
setup_schema(quiet=True)
graph_repo = GraphRepository(driver)

# Inject dependencies into server module
import llmitm_v2.monitor.server as _srv

_srv._graph_repo = graph_repo
_srv._driver = driver
set_event_callback(_push_event)

logging.getLogger(__name__).info("WSGI app ready — Neo4j connected, event callback registered")
