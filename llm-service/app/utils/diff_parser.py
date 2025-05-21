import re
from typing import List, Dict, Tuple, Optional

class DiffFile:
    """Represents a file in a diff."""
    def __init__(self, old_path: str, new_path: str):
        self.old_path = old_path
        self.new_path = new_path
        self.hunks = []
        
    def get_path(self) -> str:
        """Returns the new path unless it's /dev/null, then returns old_path."""
        return self.new_path if self.new_path != "/dev/null" else self.old_path
    
    @property
    def is_deleted(self) -> bool:
        return self.new_path == "/dev/null"
    
    @property
    def is_new(self) -> bool:
        return self.old_path == "/dev/null"

class DiffHunk:
    """Represents a hunk in a diff."""
    def __init__(self, old_start: int, old_count: int, new_start: int, new_count: int):
        self.old_start = old_start
        self.old_count = old_count
        self.new_start = new_start
        self.new_count = new_count
        self.lines = []
        
class DiffLine:
    """Represents a line in a diff."""
    def __init__(self, content: str, line_type: str, old_line_num: Optional[int] = None, new_line_num: Optional[int] = None):
        self.content = content
        self.line_type = line_type  # 'context', 'addition', 'deletion'
        self.old_line_num = old_line_num
        self.new_line_num = new_line_num

def parse_unified_diff(diff_text: str) -> List[DiffFile]:
    """
    Parse a unified diff into structured objects.
    
    Args:
        diff_text: Text of the unified diff
        
    Returns:
        List of DiffFile objects
    """
    if not diff_text:
        return []
    
    files = []
    current_file = None
    current_hunk = None
    
    # Patterns for diff parsing
    file_header_pattern = re.compile(r'^diff --git a/(.*) b/(.*)$')
    old_file_pattern = re.compile(r'^--- (?:a/)?(.*?)(?:\t.*)?$')
    new_file_pattern = re.compile(r'^\+\+\+ (?:b/)?(.*?)(?:\t.*)?$')
    hunk_header_pattern = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@')
    
    lines = diff_text.splitlines()
    old_path = None
    new_path = None
    
    for line in lines:
        # Check for file header
        file_match = file_header_pattern.match(line)
        if file_match:
            # Save previous file if it exists
            if current_file is not None:
                files.append(current_file)
            
            # Reset for new file
            old_path = None
            new_path = None
            current_file = None
            current_hunk = None
            continue
        
        # Check for old file path
        old_match = old_file_pattern.match(line)
        if old_match:
            old_path = old_match.group(1)
            continue
        
        # Check for new file path
        new_match = new_file_pattern.match(line)
        if new_match:
            new_path = new_match.group(1)
            
            # Now we have both paths, create the file
            if old_path is not None and new_path is not None:
                current_file = DiffFile(old_path, new_path)
            continue
        
        # Check for hunk header
        hunk_match = hunk_header_pattern.match(line)
        if hunk_match and current_file is not None:
            old_start = int(hunk_match.group(1))
            old_count = int(hunk_match.group(2) or 1)
            new_start = int(hunk_match.group(3))
            new_count = int(hunk_match.group(4) or 1)
            
            current_hunk = DiffHunk(old_start, old_count, new_start, new_count)
            current_file.hunks.append(current_hunk)
            
            # Initialize line numbers
            old_line_num = old_start
            new_line_num = new_start
            continue
        
        # Process content lines
        if current_hunk is not None:
            if line.startswith("+"):
                # Addition line
                current_hunk.lines.append(DiffLine(
                    content=line[1:],
                    line_type="addition",
                    old_line_num=None,
                    new_line_num=new_line_num
                ))
                new_line_num += 1
            elif line.startswith("-"):
                # Deletion line
                current_hunk.lines.append(DiffLine(
                    content=line[1:],
                    line_type="deletion",
                    old_line_num=old_line_num,
                    new_line_num=None
                ))
                old_line_num += 1
            elif line.startswith(" "):
                # Context line
                current_hunk.lines.append(DiffLine(
                    content=line[1:],
                    line_type="context",
                    old_line_num=old_line_num,
                    new_line_num=new_line_num
                ))
                old_line_num += 1
                new_line_num += 1
    
    # Add the last file
    if current_file is not None:
        files.append(current_file)
    
    return files

def get_language_from_path(file_path: str) -> Optional[str]:
    """
    Determine the programming language from a file path.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Language name or None if unknown
    """
    ext_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript (react)',
        '.tsx': 'typescript (react)',
        '.java': 'java',
        '.c': 'c',
        '.cpp': 'c++',
        '.h': 'c/c++ header',
        '.cs': 'c#',
        '.go': 'go',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.rs': 'rust',
        '.sh': 'shell',
        '.html': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.json': 'json',
        '.md': 'markdown',
        '.xml': 'xml',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.sql': 'sql',
        '.tf': 'terraform',
        '.dockerfile': 'dockerfile',
    }
    
    # Extract extension
    _, ext = file_path.lower().rsplit('.', 1) if '.' in file_path else (file_path, '')
    ext = f'.{ext}'
    
    # Special case for Dockerfile
    if file_path.lower() == 'dockerfile':
        return 'dockerfile'
    
    return ext_map.get(ext)

def chunk_diff_by_files(diff_text: str, max_chunk_size: int = 8000) -> List[Dict]:
    """
    Split a diff into chunks by files, respecting a maximum chunk size.
    
    Args:
        diff_text: The complete diff text
        max_chunk_size: Maximum characters per chunk
        
    Returns:
        List of dictionaries with file chunks
    """
    files = parse_unified_diff(diff_text)
    chunks = []
    current_chunk = ""
    current_files = []
    
    for file in files:
        file_diff = generate_file_diff(file)
        
        # If adding this file would exceed the chunk size, save the current chunk
        if len(current_chunk) + len(file_diff) > max_chunk_size and current_chunk:
            chunks.append({
                "diff": current_chunk,
                "files": current_files,
                "language": detect_common_language(current_files)
            })
            current_chunk = ""
            current_files = []
        
        current_chunk += file_diff + "\n"
        current_files.append(file.get_path())
    
    # Add the final chunk
    if current_chunk:
        chunks.append({
            "diff": current_chunk,
            "files": current_files,
            "language": detect_common_language(current_files)
        })
    
    return chunks

def generate_file_diff(file: DiffFile) -> str:
    """
    Generate a diff string for a single file.
    
    Args:
        file: DiffFile object
        
    Returns:
        Unified diff text for the file
    """
    lines = [f"--- {file.old_path}", f"+++ {file.new_path}"]
    
    for hunk in file.hunks:
        lines.append(f"@@ -{hunk.old_start},{hunk.old_count} +{hunk.new_start},{hunk.new_count} @@")
        
        for line in hunk.lines:
            prefix = " "
            if line.line_type == "addition":
                prefix = "+"
            elif line.line_type == "deletion":
                prefix = "-"
            
            lines.append(f"{prefix}{line.content}")
    
    return "\n".join(lines)

def detect_common_language(file_paths: List[str]) -> Optional[str]:
    """
    Detect the most common language among a list of files.
    
    Args:
        file_paths: List of file paths
        
    Returns:
        Most common language or None
    """
    if not file_paths:
        return None
    
    languages = {}
    for path in file_paths:
        lang = get_language_from_path(path)
        if lang:
            languages[lang] = languages.get(lang, 0) + 1
    
    if not languages:
        return None
    
    # Return the most common language
    return max(languages.items(), key=lambda x: x[1])[0]