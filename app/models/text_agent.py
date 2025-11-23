from enum import StrEnum
from pydantic import BaseModel, Field


class ActionType(StrEnum):
    """Action types that the agent can perform."""

    CREATE_SESSION = "create_session"
    CLOSE_SESSION = "close_session"
    JOIN_SESSION = "join_session"
    ASSIGN_ITEM_TO_USER = "assign_item_to_user"
    COLLECT = "trigger_collect"
    QUERY_DEBT_STATUS = "query_debt_status"
    UNKNOWN = "unknown"


class CreateSessionData(BaseModel):
    """Schema for create session action data."""

    description: str


class CloseSessionData(BaseModel):
    """Schema for close session action data."""

    session_id: int | None = None
    session_description: str | None = None


class JoinSessionData(BaseModel):
    """Schema for join session action data."""

    session_id: str = Field(..., description="UUID of the session to join")


class AssignItemToUserData(BaseModel):
    """Schema for assign item to user action data."""

    item_id: int | None = None
    user_id: int | None = None
    user_name: str | None = None
    invoice_id: int | None = None
    item_description: str | None = None


class UnknownActionData(BaseModel):
    """Schema for unknown action data."""

    reason: str | None = Field(None, description="Reason why the action could not be determined")
    suggested_action: str | None = Field(None, description="Suggested action if the intent is partially clear")


class AgentActionSchema(BaseModel):
    """Schema for agent action decision and extracted data."""

    action: ActionType
    create_session_data: CreateSessionData | None = None
    close_session_data: CloseSessionData | None = None
    join_session_data: JoinSessionData | None = None
    assign_item_to_user_data: AssignItemToUserData | None = None
    unknown_data: UnknownActionData | None = None
