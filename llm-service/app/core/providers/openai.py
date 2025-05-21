import json
import logging
from typing import Dict, List, Any, Optional

import openai
from openai import OpenAI

from app.config import settings
from app.core.llm_client import LLMClient, ReviewOptions, ReviewResult, ReviewComment
from app.core.prompt_manager import build_system_prompt

logger = logging.getLogger(__name__)

class OpenAIClient(LLMClient):
    """OpenAI implementation of the LLM client."""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        """
        Initialize the OpenAI client.
        
        Args:
            api_key: OpenAI API key
            model: Model name to use (default: gpt-4)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        logger.info(f"Initialized OpenAIClient with model {model}")
    
    async def review_code(self, diff: str, options: ReviewOptions) -> ReviewResult:
        """
        Review code diff using OpenAI.
        
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
        
        logger.debug(f"Sending request to OpenAI with {len(diff)} bytes of diff")
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=options.temperature,
                max_tokens=options.max_tokens,
                response_format={"type": "json_object"},
            )
            
            # Parse the response
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            logger.debug(f"Received response from OpenAI, used {tokens_used} tokens")
            
            # Parse JSON response
            try:
                result_data = json.loads(content)
                
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
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from OpenAI response: {e}")
                # Fallback: treat the entire response as a summary
                return ReviewResult(
                    comments=[],
                    summary=content,
                    tokens_used=tokens_used
                )
                
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            raise
    
    def get_provider_name(self) -> str:
        return "openai"
    
    def get_model_name(self) -> str:
        return self.model