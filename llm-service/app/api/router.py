import logging
from fastapi import APIRouter, Depends, HTTPException, Body

from app.api.models import ReviewRequest, ReviewResponse, ReviewComment
from app.config import settings
from app.core.llm_client import ReviewOptions as CoreReviewOptions
from app.core.providers.openai import OpenAIClient
from app.core.providers.anthropic import AnthropicClient

router = APIRouter()
logger = logging.getLogger(__name__)

async def get_llm_client(provider: str = None):
    """
    Factory function to get the appropriate LLM client.
    
    Args:
        provider: LLM provider name (default: from settings)
        
    Returns:
        LLM client instance
    """
    provider = provider or settings.DEFAULT_LLM_PROVIDER
    
    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        return OpenAIClient(api_key=settings.OPENAI_API_KEY, model=settings.OPENAI_MODEL)
    
    elif provider == "anthropic":
        if not settings.ANTHROPIC_API_KEY:
            raise HTTPException(status_code=500, detail="Anthropic API key not configured")
        return AnthropicClient(api_key=settings.ANTHROPIC_API_KEY, model=settings.ANTHROPIC_MODEL)
    
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

@router.post("/review", response_model=ReviewResponse)
async def review_code(
    request: ReviewRequest,
    provider: str = None,
    llm_client = Depends(get_llm_client)
):
    """
    Review code diff using the specified LLM provider.
    
    Args:
        request: Review request with diff and options
        provider: LLM provider to use (optional)
        
    Returns:
        Review response with comments and summary
    """
    logger.info(f"Received code review request with {len(request.diff)} bytes of diff")
    
    # Convert API options to core options
    options = CoreReviewOptions(
        max_tokens=request.options.max_tokens if request.options else settings.DEFAULT_MAX_TOKENS,
        temperature=request.options.temperature if request.options else settings.DEFAULT_TEMPERATURE,
        language=request.options.language if request.options else None,
        severity_levels=request.options.severity_levels if request.options else None,
        rules=request.options.rules if request.options else None,
        context=request.options.context if request.options else {},
    )
    
    try:
        # Perform the review
        result = await llm_client.review_code(request.diff, options)
        
        # Convert the result to API response
        return ReviewResponse(
            comments=[
                ReviewComment(
                    file=comment.file,
                    line=comment.line,
                    content=comment.content,
                    severity=comment.severity,
                    rule=comment.rule
                ) for comment in result.comments
            ],
            summary=result.summary,
            tokens_used=result.tokens_used
        )
    
    except Exception as e:
        logger.error(f"Error during code review: {e}")
        raise HTTPException(status_code=500, detail=str(e))