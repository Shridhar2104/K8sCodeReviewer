from typing import Dict, List, Optional
from pydantic import BaseModel, Field

# Request Models
class ReviewOptions(BaseModel):
    max_tokens: int = Field(default=4096, description="Maximum tokens to generate")
    temperature: float = Field(default=0.2, description="Temperature for response generation")
    language: Optional[str] = Field(default=None, description="Programming language of the code")
    severity_levels: Optional[List[str]] = Field(default=None, description="Severity levels to include")
    rules: Optional[List[str]] = Field(default=None, description="Rules to check")
    context: Optional[Dict[str, str]] = Field(default=None, description="Additional context")

class ReviewRequest(BaseModel):
    diff: str = Field(..., description="Code diff to review")
    options: Optional[ReviewOptions] = Field(default=None, description="Review options")

# Response Models
class ReviewComment(BaseModel):
    file: str = Field(..., description="File path")
    line: int = Field(..., description="Line number")
    content: str = Field(..., description="Comment content")
    severity: str = Field(..., description="Severity level")
    rule: str = Field(..., description="Rule name")

class ReviewResponse(BaseModel):
    comments: List[ReviewComment] = Field(default_factory=list, description="Review comments")
    summary: str = Field(..., description="Review summary")
    tokens_used: int = Field(..., description="Tokens used")