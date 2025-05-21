import json
import logging
from typing import Dict, List, Any, Optional

import anthropic

from app.config import settings
from app.core.llm_client import LLMClient, ReviewOptions, ReviewResult, ReviewComment
from app.core.prompt_manager import build_system_prompt

logger = logging.getLogger(__name__)

class AnthropicClient(LLMClient):
    """Anthropic implementation of the LLM client."""
    
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        """
        Initialize the Anthropic client.
        
        Args:
            api_key: Anthropic API key
            model: Model name to use (default: claude-3-opus-20240229)
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        logger.info(f"Initialized AnthropicClient with model {model}")
    
    async def review_code(self, diff: str, options: ReviewOptions) -> ReviewResult:
        """
        Review code diff using Anthropic Claude.
        
        Args:
            diff: The code diff to review
            options: Review options
            
        Returns:
            ReviewResult containing comments and summary
        """
        # Build the system prompt
        system_prompt = build_system_prompt(
            language=options.language,
            severity_levels=options.severity_levels,
            rules=options.rules
        )
        
        # Create the user prompt with the diff
        user_prompt = f"Review the following code diff:\n\n```diff\n{diff}\n```"
        
        logger.debug(f"Sending request to Anthropic with {len(diff)} bytes of diff")
        
        try:
            # Call Anthropic API
            response = self.client.messages.create(
                model=self.model,
                system=system_prompt,
                max_tokens=options.max_tokens,
                temperature=options.temperature,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Parse the response
            content = response.content[0].text
            tokens_used = (
                response.usage.input_tokens + 
                response.usage.output_tokens
            )
            
            logger.debug(f"Received response from Anthropic, used {tokens_used} tokens")
            
            # Parse JSON response
            try:
                # Find JSON in the response (Claude might wrap it in ```json ... ```)
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_content = content[json_start:json_end]
                    result_data = json.loads(json_content)
                    
                    # Extract comments
                    comments = []
                    for comment_data in result_data.get("comments", []):
                        comments.append(ReviewComment(
                            file=comment_data.get("file", ""),
                            line=comment_data.get("line", 0),
                            content=comment_data.get("content", ""),
                            severity=comment_data.get("severity", "minor"),
                            rule=comment_data.get("rule", "general")
                        ))
                    
                    # Create review result
                    return ReviewResult(
                        comments=comments,
                        summary=result_data.get("summary", "No summary provided"),
                        tokens_used=tokens_used
                    )
                else:
                    # Fallback: treat the entire response as a summary
                    return ReviewResult(
                        comments=[],
                        summary=content,
                        tokens_used=tokens_used
                    )
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from Anthropic response: {e}")
                # Fallback: treat the entire response as a summary
                return ReviewResult(
                    comments=[],
                    summary=content,
                    tokens_used=tokens_used
                )
                
        except Exception as e:
            logger.error(f"Error calling Anthropic API: {e}")
            raise
    
    def get_provider_name(self) -> str:
        return "anthropic"
    
    def get_model_name(self) -> str:
        return self.model