from pydantic import BaseModel, Field
from typing import Optional


class FounderRequest(BaseModel):
    startup_name: Optional[str] = Field(None, description="Startup name if provided")
    ask: str = Field(..., description="What the founder wants help with")
    context: Optional[str] = Field(None, description="Additional context from the founder")


class BoardMessage(BaseModel):
    role: str = Field(..., description="user, investor, or supervisor")
    speaker: str = Field(..., description="Display name for chat rendering")
    content: str = Field(..., description="Message body")
    iteration: Optional[int] = Field(None, description="Iteration number for investor/supervisor messages")


class DocumentInput(BaseModel):
    filename: str
    filetype: str
    extracted_text: str
