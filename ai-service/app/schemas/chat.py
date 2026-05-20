from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AgentName = Literal["triage", "appointment", "insurance", "knowledge", "out_of_scope"]


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    message: str = Field(min_length=1, max_length=4000)
    session_key: str = Field(min_length=1, max_length=128)


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    reply: str
    agent_used: AgentName
    session_key: str
