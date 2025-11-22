"""Agent service for natural language command processing.

This package provides functionality to process natural language commands
and execute corresponding database actions using OpenAI.

Main entry point:
    from app.services.agent import process_and_execute

    result = await process_and_execute(db, "Crear sesión para cena")
"""

from app.services.agent.executor import execute_action, process_and_execute
=

__all__ = [
    # Main entry points
    "process_and_execute",
    "execute_action",
    # Schemas
]

