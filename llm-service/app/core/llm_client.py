from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any 

class ReviewComment:
    """Reviews a single code review comment."""

    def __init__(
        self,
        file: str,
        line: int,
        content: str,
        severity: str,
        rule: str
    ):
        self.file = file
        self.line = line
        self.content = content
        self.severity = severity
        self.rule = rule
    
    def to_dict(self) -> Dict[str, Any]:
        return{
            "file": self.file,
            "line": self.line,
            "content": self.content,
            "severity": self.severity,
            "rule": self.rule

        }


class ReviewResult:
    """Represents result of code review"""

    def __init__(
        self,
        comments: List[comments],
        summary: str,
        tokens_used: int
    ):
        self.comments = comments
        self.summary = summary
        self.tokens_used = tokens_used
    
    def to_dict(self) -> Dict[str, Any]:
        return{
            "comments": self.comments,
            "summary": self.summary,
            "tokens_used": self.tokens_used
        }


class ReviewOptions:
    """Options for code review."""
    def __init__(
        self,
        max_tokens: int = 4096,
        temperature: float = 0.2,
        language: Optional[str] = None,
        severity_levels: Optional[List[str]] = None,
        rules: Optional[List[str]] = None,
        context: Optional[Dict[str, str]] = None
    ):
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.language = language
        self.severity_levels = severity_levels or ["critical", "major", "minor", "suggestion"]
        self.rules = rules or []
        self.context = context or {}



class LLMClient(ABC):
    """Base interface for LLM providers."""
    
    @abstractmethod
    async def review_code(self, diff: str, options: ReviewOptions) -> ReviewResult:
        """
        Review code diff using the LLM provider.
        
        Args:
            diff: The code diff to review
            options: Review options
            
        Returns:
            ReviewResult object containing comments and summary
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of the LLM provider."""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get the name of the model being used."""
        pass