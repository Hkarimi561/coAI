import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models import Conversation, Message, User


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RoleRef(ORM):
    id: uuid.UUID
    name: str


class UserOut(ORM):
    id: uuid.UUID
    email: str
    name: str
    is_active: bool = True
    created_at: datetime | None = None
    roles: list[RoleRef] = []
    permissions: list[str] = []  # union over all roles; the UI shows/hides features from this


class LoginIn(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=256)


class UserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=255, pattern=r"^[^@\s]+@[^@\s]+$")
    name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=256)
    role_ids: list[uuid.UUID] | None = Field(default=None, max_length=50)  # omitted -> the default "user" role


class UserUpdate(BaseModel):
    is_active: bool | None = None
    role_ids: list[uuid.UUID] | None = Field(default=None, max_length=50)  # replaces the user's roles when given
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
    mode: str = "support"
    phase: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def of(cls, c: Conversation) -> "ConversationOut":
        return cls(id=c.id, title=c.title, status=c.status, mode=c.mode, phase=(c.state or {}).get("phase", "idle"),
                   created_at=c.created_at, updated_at=c.updated_at)


class CreateConversationIn(BaseModel):
    mode: Literal["support", "teach"] = "support"


class LessonOut(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    title: str
    applies_when: str
    instruction: str
    status: str
    review_note: str
    created_at: datetime
    reviewed_at: datetime | None = None
    user: dict[str, str] | None = None

    @classmethod
    def of(cls, l, with_user: bool = False) -> "LessonOut":  # noqa: ANN001
        return cls(
            id=l.id, conversation_id=l.conversation_id, title=l.title, applies_when=l.applies_when, instruction=l.instruction,
            status=l.status, review_note=l.review_note, created_at=l.created_at, reviewed_at=l.reviewed_at,
            user={"id": str(l.user.id), "email": l.user.email, "name": l.user.name} if with_user else None,
        )


class LessonEdit(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    applies_when: str | None = Field(default=None, max_length=4000)
    instruction: str | None = Field(default=None, min_length=1, max_length=20000)
    note: str = Field(default="", max_length=2000)


class SendMessageIn(BaseModel):
    content: str = Field(min_length=1, max_length=20000)
    refresh: bool = False  # search again: skip the answer cache and cached web research


class FeedbackIn(BaseModel):
    message_id: uuid.UUID
    outcome: Literal["confirmed", "rejected"]
    note: str = Field(default="", max_length=2000)


class FeedbackOut(BaseModel):
    conversation: ConversationOut
    message: MessageOut | None = None


def user_out(u: User) -> UserOut:
    return UserOut.model_validate(u)
