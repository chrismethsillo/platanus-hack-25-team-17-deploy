"""Action executor for agent service."""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agent.processor import process_user_command
from app.models.text_agent import AgentActionSchema

logger = logging.getLogger(__name__)


async def execute_action(db: AsyncSession, action_schema: AgentActionSchema) -> Any:
    """Execute the action determined by the agent.

    This function routes the action to the appropriate handler based on the
    action type in the schema.

    Args:
        db: Database session
        action_schema: Agent action schema with action type and data

    Returns:
        Result of the executed action (Session, Item, etc.)

    Raises:
        ValueError: If action type is not supported or required data is missing
        KeyError: If action handler is not found in mapping
    """
    action_type = action_schema.action

    if action_type not in ACTION_HANDLERS:
        raise ValueError(f"Action handler not found for action type: {action_type.value}")

    handler = ACTION_HANDLERS[action_type]
    logger.info(f"Executing action handler for: {action_type.value}")

    return await handler(db, action_schema)


def process_and_execute(db: AsyncSession, user_text: str) -> Any:
    action_schema = process_user_command(user_text)

    result = execute_action(db, action_schema)

    logger.info(f"Successfully processed and executed action: {action_schema.action.value}")

    return result
