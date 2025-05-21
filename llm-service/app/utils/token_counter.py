import tiktoken
from typing import Dict, List, Optional, Tuple

# Default models for common providers
DEFAULT_MODELS = {
    "openai": "gpt-4",
    "anthropic": "claude-3-opus-20240229"
}

# Tiktoken encoding for OpenAI models
MODEL_TO_ENCODING = {
    "gpt-3.5-turbo": "cl100k_base",
    "gpt-4": "cl100k_base",
    "gpt-4-turbo": "cl100k_base",
}

def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Count the number of tokens in a text for a specific model.
    
    Args:
        text: The text to count tokens for
        model: The model name
        
    Returns:
        Number of tokens
    """
    try:
        # Get the encoding name for the model
        encoding_name = MODEL_TO_ENCODING.get(model, "cl100k_base")
        
        # Get the encoding
        encoding = tiktoken.get_encoding(encoding_name)
        
        # Count tokens
        tokens = encoding.encode(text)
        return len(tokens)
    except Exception:
        # Fallback: estimate tokens as words/0.75
        return int(len(text.split()) / 0.75)

def optimize_diff_context(diff_text: str, max_tokens: int = 6000, model: str = "gpt-4") -> str:
    """
    Optimize a diff by trimming context lines to fit within token limits.
    
    Args:
        diff_text: Original diff text
        max_tokens: Maximum token limit
        model: Model to count tokens for
        
    Returns:
        Optimized diff text
    """
    # Parse the diff
    files = parse_unified_diff(diff_text)
    
    # Calculate current tokens
    current_tokens = count_tokens(diff_text, model)
    
    # If already under limit, return as is
    if current_tokens <= max_tokens:
        return diff_text
    
    # Strategy 1: Reduce context lines while preserving all changes
    reduced_context_files = []
    for file in files:
        reduced_file = DiffFile(file.old_path, file.new_path)
        
        for hunk in file.hunks:
            reduced_hunk = DiffHunk(hunk.old_start, hunk.old_count, hunk.new_start, hunk.new_count)
            
            # Keep only essential context lines (one before and after changes)
            essential_lines = []
            context_blocks = []
            current_block = {"type": None, "lines": []}
            
            for line in hunk.lines:
                # Track blocks of context vs. changes
                if line.line_type != current_block["type"]:
                    if current_block["lines"]:
                        context_blocks.append(current_block)
                    current_block = {"type": line.line_type, "lines": [line]}
                else:
                    current_block["lines"].append(line)
            
            # Add the last block
            if current_block["lines"]:
                context_blocks.append(current_block)
            
            # Process blocks to keep changes and minimal context
            for i, block in enumerate(context_blocks):
                if block["type"] in ["addition", "deletion"]:
                    # Keep all change lines
                    essential_lines.extend(block["lines"])
                elif block["type"] == "context":
                    if i == 0 or i == len(context_blocks) - 1:
                        # Keep at most 2 context lines at the beginning or end
                        essential_lines.extend(block["lines"][:min(2, len(block["lines"]))])
                    else:
                        # Keep at most 1 context line before and after changes
                        if len(block["lines"]) <= 2:
                            essential_lines.extend(block["lines"])
                        else:
                            essential_lines.append(block["lines"][0])
                            essential_lines.append(block["lines"][-1])
            
            reduced_hunk.lines = essential_lines
            reduced_file.hunks.append(reduced_hunk)
        
        reduced_context_files.append(reduced_file)
    
    # Generate the reduced diff
    reduced_diff = "".join(generate_file_diff(file) + "\n" for file in reduced_context_files)
    
    # Check if we're now under the limit
    reduced_tokens = count_tokens(reduced_diff, model)
    if reduced_tokens <= max_tokens:
        return reduced_diff
    
    # Strategy 2: If still over limit, focus on the most relevant files
    # (files with the most changes)
    file_relevance = []
    for file in reduced_context_files:
        change_count = sum(
            1 for hunk in file.hunks 
            for line in hunk.lines 
            if line.line_type in ["addition", "deletion"]
        )
        file_relevance.append((file, change_count))
    
    # Sort files by relevance (most changes first)
    file_relevance.sort(key=lambda x: x[1], reverse=True)
    
    # Add files until we reach the token limit
    final_files = []
    current_tokens = 0
    
    for file, _ in file_relevance:
        file_diff = generate_file_diff(file)
        file_tokens = count_tokens(file_diff, model)