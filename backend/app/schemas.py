import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models import Conversation, Message, User


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserOut(ORM):
    id: uuid.UUID
    email: str
    name: str
    role: str
    is_active: bool = True
    created_at: datetime | None = None


class LoginIn(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=256)


class UserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=255, pattern=r"^[^@\s]+@[^@\s]+$")
    name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=256)
    role: Literal["admin", "user"] = "user"


class UserUpdate(BaseModel):
    is_active: bool | None = None
    role: Literal["admin", "user"] | None = None
    password: str | None = Field(default=None, min_length=8, max_length=256)


class MessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    citations: list[dict[str, Any]]
    meta: dict[str, Any]
    created_at: datetime

    @classmethod
    def of(cls, m: Message) -> "MessageOut":
        return cls(id=m.id, role=m.role, content=m.content, citations=m.citations or [], meta=m.meta or {}, created_at=m.created_at)


class ConversationOut(BaseModel):
    id: uuid.UUID
    title: str
    status: str
    phase: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def of(cls, c: Conversation) -> "ConversationOut":
        return cls(id=c.id, title=c.title, status=c.status, phase=(c.state or {}).get("phase", "idle"),
                   created_at=c.created_at, updated_at=c.updated_at)


class SendMessageIn(BaseModel):
    content: str = Field(min_length=1, max_length=20000)


class FeedbackIn(BaseModel):
    message_id: uuid.UUID
    outcome: Literal["confirmed", "rejected"]
    note: str = Field(default="", max_length=2000)


class FeedbackOut(BaseModel):
    conversation: ConversationOut
    message: MessageOut | None = None


def user_out(u: User) -> UserOut:
    return UserOut.model_validate(u)
