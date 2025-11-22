from pydantic import BaseModel, root_validator, Field
from enum import StrEnum
from typing import Literal
from datetime import datetime, timezone


class KapsoMessageType(StrEnum):
    TEXT = "text"
    INTERACTIVE = "interactive"
    IMAGE = "image"


class KapsoInteractiveType(StrEnum):
    LIST = "list"
    BUTTON = "button"


class BaseKapsoBody(BaseModel):
    messaging_product: Literal["whatsapp"] = "whatsapp"
    to: str
    type: KapsoMessageType


class KapsoBody(BaseModel):
    body: str


class KapsoReply(BaseModel):
    id: str
    title: str


class KapsoButton(BaseModel):
    type: Literal["reply"] = "reply"
    reply: KapsoReply


class KapsoRow(BaseModel):
    id: str
    title: str
    description: str


class KapsoSection(BaseModel):
    title: str
    rows: list[KapsoRow]


class KapsoAction(BaseModel):
    buttons: list[KapsoButton] | None = None
    sections: list[KapsoSection] | None = None
    button: KapsoButton | None = None

    @root_validator(pre=True)
    def validate_action(cls, values):
        buttons = values.get("buttons")
        sections = values.get("sections")
        button = values.get("button")

        # Validation: either (sections and button) or (buttons)
        if (sections is not None and button is not None) and (buttons is None):
            return values
        elif (buttons is not None) and (sections is None and button is None):
            return values
        else:
            raise ValueError(
                "KapsoAction must have either both 'sections' and 'button', or 'buttons' (not both or partial)."
            )


class KapsoInteractiveBody(BaseModel):
    type: KapsoInteractiveType
    body: KapsoBody
    action: KapsoAction


class KapsoInteractiveMessage(BaseKapsoBody):
    interactive: KapsoInteractiveBody


class KapsoTextMessage(BaseKapsoBody):
    text: KapsoBody


class KapsoImage(BaseModel):
    link: str


class KapsoConversation(BaseModel):
    contact_name: str
    phone_number: str


class KapsoMessage(BaseModel):
    id: str
    sender: str = Field(..., alias="from")
    received_at: datetime = datetime.now(tz=timezone.utc).replace(tzinfo=None)
    text: KapsoBody | None = None
    image: KapsoImage | None = None

    def is_image(self) -> bool:
        return self.image is not None

    def is_text(self) -> bool:
        return self.text is not None


class KapsoWebhookMessageReceived(BaseModel):
    message: KapsoMessage
    conversation: KapsoConversation
