from typing import List, Optional

def build_system_prompt(
    language: Optional[str] = None,
    severity_levels: Optional[List[str]] = None,
    rules: Optional[List[str]] = None
) -> str:
    """
    Build a system prompt for code review.
    
    Args:
        language: Programming language of the code
        severity_levels: Severity levels to check
        rules: Rules to check
        
    Returns:
        System prompt for the LLM
    """
    prompt = [
        "You are an expert code reviewer with deep knowledge of software development best practices, security, and performance optimization.",
        "\nYour task is to review the provided code diff and provide specific, actionable feedback."
    ]
    
    # Add language context if provided
    if language:
        prompt.append(f"\nThe code is written in {language}.")
    
    # Explain the response format
    prompt.append("""
Your response MUST be in the following JSON format:
{
  "comments": [
    {
      "file": "path/to/file.ext",
      "line": 123,
      "content": "Your detailed feedback here. Be specific and actionable.",
      "severity": "critical|major|minor|suggestion",
      "rule": "security|performance|maintainability|etc"
    }
  ],
  "summary": "A concise summary of your findings and overall assessment."
}""")
    
    # Explain severity levels
    prompt.append("""
Severity levels:
- critical: Issues that must be fixed immediately (security vulnerabilities, data corruption risks)
- major: Significant issues that should be addressed (bugs, performance problems)
- minor: Less important issues (style problems, minor inefficiencies)
- suggestion: Optional improvements""")
    
    # Add severity filter if provided
    if severity_levels:
        prompt.append(f"\nOnly include issues with these severity levels: {', '.join(severity_levels)}")
    
    # Add rules filter if provided
    if rules:
        prompt.append(f"\nFocus on these specific areas: {', '.join(rules)}")
    
    return "\n".join(prompt)