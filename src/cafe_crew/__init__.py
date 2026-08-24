"""Cafe research crew package."""

import os


# Web processes must never stop for CrewAI's first-run tracing prompt.
os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")
