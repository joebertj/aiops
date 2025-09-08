"""
File Agent for awesh - Intelligent file detection and context injection

This agent processes user prompts to detect file references and automatically
injects relevant file content into the AI prompt for better context.

Features:
- Exact filename matching
- Partial filename matching (ignoring extensions)
- Fuzzy filename matching using grep patterns
- Smart content extraction (head/tail/targeted lines)
- File type-aware content limiting
- Multiple file handling
"""

import os
import sys
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

# Global verbose setting - shared with server.py
VERBOSE = os.getenv('VERBOSE', '0') != '0'

def debug_log(message):
    """Log debug message if verbose mode is enabled"""
    global VERBOSE
    if VERBOSE:
        print(f"🔍 File Agent: {message}", file=sys.stderr)


@dataclass
class FileMatch:
    """Represents a matched file with metadata"""
    path: str
    match_type: str  # 'exact', 'partial', 'fuzzy'
    confidence: float
    size: int
    lines: int


class FileAgent:
    """Intelligent file detection and context injection agent"""
    
    def __init__(self, max_file_size: int = 50000, max_total_content: int = 10000, 
                 max_files: int = 5, enabled: bool = True):
        self.max_file_size = max_file_size  # Max size per file to process
        self.max_total_content = max_total_content  # Max total content to inject
        self.max_files = max_files  # Max number of files to include
        self.enabled = enabled
        self.current_dir = os.getcwd()
        
        # File patterns that likely indicate file references
        self.file_patterns = [
            r'\b[\w\-\.]+\.(py|js|ts|jsx|tsx|go|rs|c|cpp|h|hpp|java|rb|php|sh|bash|zsh|fish|yml|yaml|json|xml|html|css|scss|sass|md|txt|log|conf|cfg|ini|env|dockerfile|makefile|gemfile|package\.json|requirements\.txt|cargo\.toml|go\.mod)\b',
            r'\b[\w\-\.]+/[\w\-\.]+\b',  # path-like patterns
            r'\.?/[\w\-\./]+\b',  # relative paths
            r'~/[\w\-\./]+\b',  # home-relative paths
        ]
        
        # Binary file extensions to skip
        self.binary_extensions = {
            '.bin', '.exe', '.dll', '.so', '.dylib', '.o', '.a', '.lib',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg',
            '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.zip', '.tar', '.gz', '.bz2', '.xz', '.rar', '.7z',
            '.pyc', '.pyo', '.class', '.jar', '.war'
        }
    
    
    async def process_prompt(self, prompt: str, working_dir: str = None) -> Tuple[str, bool]:
        """
        Process user prompt to detect file references and inject context
        
        Returns:
            Tuple[enhanced_prompt, files_found]
        """
        if not self.enabled:
            return prompt, False
            
        if working_dir:
            self.current_dir = working_dir
            
        debug_log(f"Processing prompt in directory: {self.current_dir}")
        
        # Extract potential file references from prompt
        file_candidates = self._extract_file_candidates(prompt)
        
        if not file_candidates:
            debug_log("No file candidates found in prompt")
            return prompt, False
            
        debug_log(f"Found {len(file_candidates)} file candidates: {file_candidates}")
        
        # Search for actual files
        file_matches = await self._search_files(file_candidates)
        
        if not file_matches:
            debug_log("No actual files found for candidates")
            return prompt, False
            
        debug_log(f"Found {len(file_matches)} file matches")
        
        # Extract and inject file content
        enhanced_prompt = await self._inject_file_context(prompt, file_matches)
        
        return enhanced_prompt, True
    
    def _extract_file_candidates(self, prompt: str) -> List[str]:
        """Extract potential file references from the prompt and verify they exist"""
        potential_candidates = set()
        
        # Apply each pattern
        for pattern in self.file_patterns:
            matches = re.findall(pattern, prompt, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    # For patterns with groups, take the full match
                    full_match = re.search(pattern, prompt, re.IGNORECASE)
                    if full_match:
                        potential_candidates.add(full_match.group(0))
                else:
                    potential_candidates.add(match)
        
        # Look for words that are likely filenames (more restrictive)
        words = prompt.split()
        for word in words:
            # Clean word of punctuation
            clean_word = re.sub(r'[^\w\-\./]', '', word)
            if clean_word and self._is_likely_filename(clean_word):
                potential_candidates.add(clean_word)
        
        # Verify candidates actually exist in filesystem
        verified_candidates = []
        for candidate in potential_candidates:
            if self._candidate_exists_in_filesystem(candidate):
                verified_candidates.append(candidate)
                debug_log(f"Verified file candidate: {candidate}")
            else:
                debug_log(f"Rejected candidate (not found): {candidate}")
        
        return verified_candidates
    
    def _is_likely_filename(self, word: str) -> bool:
        """Check if a word is likely to be a filename"""
        # Skip common English words that are not filenames
        common_words = {
            'tell', 'me', 'about', 'what', 'is', 'the', 'this', 'that',
            'how', 'why', 'when', 'where', 'who', 'can', 'will', 'would',
            'should', 'could', 'do', 'does', 'did', 'have', 'has', 'had',
            'are', 'was', 'were', 'be', 'been', 'being', 'get', 'got',
            'make', 'made', 'take', 'took', 'come', 'came', 'go', 'went',
            'see', 'saw', 'know', 'knew', 'think', 'thought', 'say', 'said',
            'give', 'gave', 'find', 'found', 'use', 'used', 'work', 'works',
            'run', 'runs', 'ran', 'show', 'shows', 'showed', 'help', 'helps',
            'need', 'needs', 'want', 'wants', 'like', 'likes', 'look', 'looks',
            'try', 'tries', 'tried', 'start', 'starts', 'started', 'stop',
            'stops', 'stopped', 'open', 'opens', 'opened', 'close', 'closes',
            'closed', 'read', 'reads', 'write', 'writes', 'wrote', 'create',
            'creates', 'created', 'delete', 'deletes', 'deleted', 'update',
            'updates', 'updated', 'change', 'changes', 'changed', 'fix',
            'fixes', 'fixed', 'check', 'checks', 'checked', 'test', 'tests',
            'tested', 'install', 'installs', 'installed', 'remove', 'removes',
            'removed', 'add', 'adds', 'added', 'edit', 'edits', 'edited',
            'modify', 'modifies', 'modified', 'build', 'builds', 'built',
            'deploy', 'deploys', 'deployed', 'configure', 'configures', 'configured'
        }
        
        word_lower = word.lower()
        
        # Skip common words
        if word_lower in common_words:
            return False
            
        # Must have file-like characteristics
        return (
            '.' in word or  # Has extension
            '/' in word or  # Has path separator
            (len(word) > 4 and word_lower.endswith(('py', 'js', 'ts', 'go', 'rs', 'c', 'h', 'cpp', 'java', 'rb', 'php', 'sh', 'yml', 'yaml', 'json', 'xml', 'html', 'css', 'md', 'txt', 'log', 'conf', 'cfg', 'ini', 'env'))) or  # Common file endings
            (len(word) > 6 and not word_lower.isalpha())  # Long word with non-alpha chars (likely filename)
        )
    
    def _candidate_exists_in_filesystem(self, candidate: str) -> bool:
        """Check if a candidate actually exists in the filesystem"""
        try:
            # Try as-is first
            if os.path.isfile(candidate):
                return True
            
            # Try with current directory
            full_path = os.path.join(self.current_dir, candidate)
            if os.path.isfile(full_path):
                return True
            
            # For candidates without extensions, try common extensions
            if '.' not in candidate:
                common_extensions = ['.py', '.js', '.ts', '.go', '.rs', '.c', '.cpp', '.h', 
                                   '.java', '.rb', '.php', '.sh', '.yml', '.yaml', '.json', 
                                   '.xml', '.html', '.css', '.md', '.txt', '.log', '.conf', 
                                   '.cfg', '.ini', '.env']
                
                for ext in common_extensions:
                    test_path = os.path.join(self.current_dir, candidate + ext)
                    if os.path.isfile(test_path):
                        return True
            
            return False
        except Exception:
            return False
    
    async def _search_files(self, candidates: List[str]) -> List[FileMatch]:
        """Search for actual files matching the candidates"""
        matches = []
        
        for candidate in candidates:
            # Try exact match first
            exact_matches = await self._find_exact_matches(candidate)
            matches.extend(exact_matches)
            
            # Try partial matches (ignoring extensions)
            if not exact_matches:
                partial_matches = await self._find_partial_matches(candidate)
                matches.extend(partial_matches)
            
            # Try fuzzy matches if still nothing
            if not exact_matches and not partial_matches:
                fuzzy_matches = await self._find_fuzzy_matches(candidate)
                matches.extend(fuzzy_matches)
        
        # Remove duplicates and sort by confidence
        unique_matches = {}
        for match in matches:
            if match.path not in unique_matches or match.confidence > unique_matches[match.path].confidence:
                unique_matches[match.path] = match
        
        sorted_matches = sorted(unique_matches.values(), key=lambda x: x.confidence, reverse=True)
        return sorted_matches[:self.max_files]
    
    async def _find_exact_matches(self, candidate: str) -> List[FileMatch]:
        """Find exact filename matches"""
        matches = []
        
        # Try as-is
        if await self._file_exists_and_readable(candidate):
            match = await self._create_file_match(candidate, 'exact', 1.0)
            if match:
                matches.append(match)
        
        # Try with current directory
        full_path = os.path.join(self.current_dir, candidate)
        if await self._file_exists_and_readable(full_path):
            match = await self._create_file_match(full_path, 'exact', 0.9)
            if match:
                matches.append(match)
        
        return matches
    
    async def _find_partial_matches(self, candidate: str) -> List[FileMatch]:
        """Find partial matches ignoring extensions"""
        matches = []
        base_name = os.path.splitext(candidate)[0]
        
        try:
            # Use find to search for files with matching base name
            cmd = f"find {self.current_dir} -maxdepth 3 -type f -name '{base_name}*' 2>/dev/null"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            
            for line in result.stdout.strip().split('\n'):
                if line and await self._file_exists_and_readable(line):
                    match = await self._create_file_match(line, 'partial', 0.7)
                    if match:
                        matches.append(match)
        except subprocess.TimeoutExpired:
            debug_log(f"Timeout searching for partial matches of {candidate}")
        except Exception as e:
            debug_log(f"Error in partial search: {e}")
        
        return matches
    
    async def _find_fuzzy_matches(self, candidate: str) -> List[FileMatch]:
        """Find fuzzy matches using grep-like patterns"""
        matches = []
        
        try:
            # Use find with grep to search file contents and names
            cmd = f"find {self.current_dir} -maxdepth 2 -type f -name '*{candidate}*' 2>/dev/null | head -10"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            
            for line in result.stdout.strip().split('\n'):
                if line and await self._file_exists_and_readable(line):
                    match = await self._create_file_match(line, 'fuzzy', 0.5)
                    if match:
                        matches.append(match)
        except subprocess.TimeoutExpired:
            debug_log(f"Timeout searching for fuzzy matches of {candidate}")
        except Exception as e:
            debug_log(f"Error in fuzzy search: {e}")
        
        return matches
    
    async def _file_exists_and_readable(self, path: str) -> bool:
        """Check if file exists and is readable, not binary"""
        try:
            if not os.path.isfile(path):
                return False
            
            # Skip binary files
            ext = os.path.splitext(path)[1].lower()
            if ext in self.binary_extensions:
                return False
            
            # Check if file is readable
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                f.read(1)  # Try to read one character
            
            return True
        except:
            return False
    
    async def _create_file_match(self, path: str, match_type: str, confidence: float) -> Optional[FileMatch]:
        """Create a FileMatch object with metadata"""
        try:
            stat = os.stat(path)
            size = stat.st_size
            
            # Skip very large files
            if size > self.max_file_size:
                debug_log(f"Skipping large file: {path} ({size} bytes)")
                return None
            
            # Count lines for text files
            lines = 0
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = sum(1 for _ in f)
            except:
                lines = 0
            
            return FileMatch(
                path=path,
                match_type=match_type,
                confidence=confidence,
                size=size,
                lines=lines
            )
        except Exception as e:
            debug_log(f"Error creating file match for {path}: {e}")
            return None
    
    async def _inject_file_context(self, prompt: str, file_matches: List[FileMatch]) -> str:
        """Inject file content into the prompt"""
        file_contexts = []
        total_content_size = 0
        
        for match in file_matches:
            if total_content_size >= self.max_total_content:
                break
                
            content = await self._extract_file_content(match)
            if content:
                remaining_space = self.max_total_content - total_content_size
                if len(content) > remaining_space:
                    content = content[:remaining_space] + "\n... [truncated]"
                
                file_contexts.append(f"""
=== File: {match.path} ===
Match: {match.match_type} (confidence: {match.confidence:.1f})
Size: {match.size} bytes, Lines: {match.lines}

{content}
=== End of {os.path.basename(match.path)} ===
""")
                total_content_size += len(content)
        
        if not file_contexts:
            return prompt
        
        # Inject context before the original prompt
        enhanced_prompt = f"""FILE CONTEXT:
The user mentioned files in their request. Here are the relevant files found:

{''.join(file_contexts)}

ORIGINAL USER REQUEST:
{prompt}

Please use the file content above to provide more accurate and context-aware responses. If you provide commands, format them as:
awesh: <command>"""
        
        debug_log(f"Enhanced prompt with {len(file_matches)} files, {total_content_size} chars of content")
        return enhanced_prompt
    
    async def _extract_file_content(self, match: FileMatch) -> str:
        """Extract relevant content from a file"""
        try:
            with open(match.path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # For small files, return everything
            if len(content) <= 2000:
                return content
            
            # For larger files, use smart extraction
            lines = content.split('\n')
            
            # If file has many lines, show head + tail + middle sample
            if len(lines) > 100:
                head = '\n'.join(lines[:20])
                tail = '\n'.join(lines[-10:])
                middle_start = len(lines) // 2 - 5
                middle = '\n'.join(lines[middle_start:middle_start + 10])
                
                return f"""{head}

... [showing lines {middle_start + 1}-{middle_start + 10} of {len(lines)}] ...
{middle}

... [showing last 10 lines] ...
{tail}"""
            else:
                # Medium files - show more content
                return content[:3000] + ("\n... [truncated]" if len(content) > 3000 else "")
                
        except Exception as e:
            debug_log(f"Error reading file {match.path}: {e}")
            return f"[Error reading file: {e}]"
