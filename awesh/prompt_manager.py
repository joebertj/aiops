"""
Enhanced Prompt Manager for awesh

Implements kubens/kubectx/kube-ps1 style prompts with context information on a new line.
Shows: <context>:<namespace>:<others> on the first line, then awesh> on the second line.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

# Import process monitor for security warnings
try:
    from .process_monitor import scan_processes_for_prompt
    HAVE_PROCESS_MONITOR = True
except ImportError:
    HAVE_PROCESS_MONITOR = False

# Import RAG system for context enhancement
try:
    from .rag_system import enhance_prompt_with_context
    HAVE_RAG_SYSTEM = True
except ImportError:
    HAVE_RAG_SYSTEM = False


class PromptManager:
    """
    Manages enhanced prompts with context information similar to kubens/kubectx/kube-ps1.
    
    Prompt format:
    [context:namespace:others]
    awesh> 
    
    This provides clear context information without cluttering the main prompt line.
    """
    
    def __init__(self):
        self.current_context = {}
        self._kubectl_available = self._check_kubectl_available()
    
    def _check_kubectl_available(self) -> bool:
        """Check if kubectl is available"""
        try:
            subprocess.run(['kubectl', 'version', '--client'], 
                         capture_output=True, timeout=5)
            return True
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def get_kubectl_context(self) -> Optional[str]:
        """Get current kubectl context"""
        if not self._kubectl_available:
            return None
        
        try:
            result = subprocess.run(['kubectl', 'config', 'current-context'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass
        return None
    
    def get_kubectl_namespace(self) -> Optional[str]:
        """Get current kubectl namespace"""
        if not self._kubectl_available:
            return None
        
        try:
            result = subprocess.run(['kubectl', 'config', 'view', '--minify', '--output', 'jsonpath={..namespace}'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass
        return None
    
    def get_git_branch(self) -> Optional[str]:
        """Get current git branch"""
        try:
            result = subprocess.run(['git', 'branch', '--show-current'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                branch = result.stdout.strip()
                if branch:
                    return branch
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass
        return None
    
    def get_git_status(self) -> Optional[str]:
        """Get git status indicators"""
        try:
            # Check for uncommitted changes
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                if result.stdout.strip():
                    return "*"  # Has uncommitted changes
                else:
                    return "✓"  # Clean working directory
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass
        return None
    
    def get_working_directory(self) -> str:
        """Get current working directory with home directory shortening"""
        cwd = Path.cwd()
        home = Path.home()
        
        try:
            # Try to get relative path from home
            relative = cwd.relative_to(home)
            return f"~/{relative}"
        except ValueError:
            # Not under home directory
            return str(cwd)
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get current environment information"""
        info = {
            'cwd': self.get_working_directory(),
            'kubectl_context': self.get_kubectl_context(),
            'kubectl_namespace': self.get_kubectl_namespace(),
            'git_branch': self.get_git_branch(),
            'git_status': self.get_git_status(),
            'user': os.getenv('USER', 'unknown'),
            'host': os.getenv('HOSTNAME', os.uname().nodename if hasattr(os, 'uname') else 'unknown')
        }
        return info
    
    def format_context_line(self, info: Dict[str, Any]) -> str:
        """
        Format the context line similar to kubens/kubectx/kube-ps1.
        
        Format: [context:namespace:others]
        """
        context_parts = []
        
        # Add kubectl context if available
        if info['kubectl_context']:
            context_parts.append(info['kubectl_context'])
        
        # Add kubectl namespace if available and different from default
        if info['kubectl_namespace'] and info['kubectl_namespace'] != 'default':
            context_parts.append(info['kubectl_namespace'])
        
        # Add git branch if available
        if info['git_branch']:
            git_info = info['git_branch']
            if info['git_status']:
                git_info += info['git_status']
            context_parts.append(f"git:{git_info}")
        
        # Add working directory (shortened)
        context_parts.append(info['cwd'])
        
        # Format as [part1:part2:part3]
        if context_parts:
            return f"[{':'.join(context_parts)}]"
        else:
            return f"[{info['cwd']}]"
    
    def get_prompt(self, ai_ready: bool = False, user_input: str = "") -> str:
        """
        Get the complete prompt with context information and dynamic prompt based on user input.
        
        Format: AI:user@host:~:<ctx>:<ns>:<others>:<dynamic>:<based>:<on>:<user>:<prompt>
                > 
        
        Args:
            ai_ready: Whether AI is ready (shows AI prefix)
            user_input: User's input to determine dynamic prompt components
            
        Returns:
            Formatted prompt string
        """
        # Get environment information
        info = self.get_environment_info()
        
        # Build context parts
        context_parts = []
        
        # Add kubectl context if available
        if info['kubectl_context']:
            context_parts.append(info['kubectl_context'])
        
        # Add kubectl namespace if available and different from default
        if info['kubectl_namespace'] and info['kubectl_namespace'] != 'default':
            context_parts.append(info['kubectl_namespace'])
        
        # Add git branch if available
        if info['git_branch']:
            git_info = info['git_branch']
            if info['git_status']:
                git_info += info['git_status']
            context_parts.append(f"git:{git_info}")
        
        # Add dynamic prompt components based on user input
        dynamic_parts = self._get_dynamic_prompt_parts(user_input)
        context_parts.extend(dynamic_parts)
        
        # Build the first line: AI:user@host:~:<ctx>:<ns>:<others>:<dynamic>:<based>:<on>:<user>:<prompt>
        first_line_parts = []
        
        # Add AI prefix if ready
        if ai_ready:
            first_line_parts.append("AI")
        
        # Add user@host
        first_line_parts.append(f"{info['user']}@{info['host']}")
        
        # Add working directory (shortened)
        first_line_parts.append(info['cwd'])
        
        # Add context information
        first_line_parts.extend(context_parts)
        
        # Join with colons
        first_line = ":".join(first_line_parts)
        
        # Add process monitoring warnings in RED
        if HAVE_PROCESS_MONITOR:
            try:
                process_warning = scan_processes_for_prompt()
                if process_warning:
                    # Add process warning in RED (using ANSI escape codes)
                    first_line += f" \033[91m{process_warning}\033[0m"
            except Exception as e:
                # Silently fail if process monitoring has issues
                pass
        
        # Return two-line prompt: first line with context, second line just >
        return f"{first_line}\n>"
    
    def get_enhanced_prompt_with_rag(self, ai_ready: bool = False, user_input: str = "") -> str:
        """
        Get prompt with RAG-enhanced context for AI queries.
        
        Args:
            ai_ready: Whether AI is ready
            user_input: User's input to enhance with RAG context
            
        Returns:
            Enhanced prompt with RAG context
        """
        # Get the base prompt
        base_prompt = self.get_prompt(ai_ready, user_input)
        
        # If we have RAG system and user input, enhance with context
        if HAVE_RAG_SYSTEM and user_input.strip():
            try:
                enhanced_input = enhance_prompt_with_context(user_input, max_context_length=300)
                return f"{base_prompt}{enhanced_input}"
            except Exception as e:
                # Silently fail if RAG enhancement has issues
                pass
        
        return base_prompt
    
    def _get_dynamic_prompt_parts(self, user_input: str) -> list:
        """
        Generate dynamic prompt parts based on user input with specific context.
        
        Examples:
        - Kubernetes: <ctx>:<ns>
        - Network: <url>
        - Disk: <high usage mount>
        
        Args:
            user_input: User's input to analyze
            
        Returns:
            List of dynamic prompt components
        """
        dynamic_parts = []
        user_lower = user_input.lower().strip()
        
        # Kubernetes-related prompts - show context and namespace
        if any(word in user_lower for word in ['kubernetes', 'k8s', 'kube', 'pod', 'deployment', 'service', 'namespace']):
            info = self.get_environment_info()
            if info['kubectl_context']:
                dynamic_parts.append(f"<{info['kubectl_context']}>")
            if info['kubectl_namespace'] and info['kubectl_namespace'] != 'default':
                dynamic_parts.append(f"<{info['kubectl_namespace']}>")
            if not dynamic_parts:  # If no k8s context, show generic k8s
                dynamic_parts.append("<k8s>")
        
        # Network/URL prompts - extract and show URL
        elif any(word in user_lower for word in ['curl', 'wget', 'http', 'https', 'api', 'url']):
            url = self._extract_url_from_input(user_input)
            if url:
                dynamic_parts.append(f"<{url}>")
            else:
                dynamic_parts.append("<url>")
        
        # Disk/mount prompts - show high usage mount
        elif any(word in user_lower for word in ['disk', 'space', 'usage', 'mount', 'df', 'storage']):
            high_usage_mount = self._get_high_usage_mount()
            if high_usage_mount:
                dynamic_parts.append(f"<{high_usage_mount}>")
            else:
                dynamic_parts.append("<disk>")
        
        # Git-related prompts
        elif any(word in user_lower for word in ['git', 'commit', 'branch', 'merge', 'push', 'pull']):
            info = self.get_environment_info()
            if info['git_branch']:
                git_info = info['git_branch']
                if info['git_status']:
                    git_info += info['git_status']
                dynamic_parts.append(f"<{git_info}>")
            else:
                dynamic_parts.append("<git>")
        
        # System/Process prompts
        elif any(word in user_lower for word in ['system', 'process', 'memory', 'cpu', 'ps', 'top']):
            dynamic_parts.append("<sys>")
        
        # Security prompts
        elif any(word in user_lower for word in ['security', 'permission', 'access', 'auth', 'login']):
            dynamic_parts.append("<sec>")
        
        # Development prompts
        elif any(word in user_lower for word in ['code', 'debug', 'test', 'build', 'compile', 'run']):
            dynamic_parts.append("<dev>")
        
        # Database prompts
        elif any(word in user_lower for word in ['database', 'db', 'sql', 'query', 'table', 'data']):
            dynamic_parts.append("<db>")
        
        # File operations
        elif any(word in user_lower for word in ['file', 'directory', 'folder', 'ls', 'cat', 'grep', 'find']):
            dynamic_parts.append("<file>")
        
        # Docker/Container prompts
        elif any(word in user_lower for word in ['docker', 'container', 'image', 'run', 'build', 'compose']):
            dynamic_parts.append("<docker>")
        
        # Monitoring/Logs
        elif any(word in user_lower for word in ['log', 'monitor', 'watch', 'tail', 'status', 'health']):
            dynamic_parts.append("<monitor>")
        
        # If no specific context detected, no dynamic parts
        # (don't add "general" - keep it clean)
        
        return dynamic_parts
    
    def _extract_url_from_input(self, user_input: str) -> str:
        """
        Extract URL from user input for network operations.
        
        Args:
            user_input: User's input
            
        Returns:
            Extracted URL or empty string
        """
        import re
        
        # Look for URLs in the input
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, user_input)
        
        if urls:
            # Return the first URL, truncated if too long
            url = urls[0]
            if len(url) > 30:
                return url[:27] + "..."
            return url
        
        # Look for domain names
        domain_pattern = r'[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        domains = re.findall(domain_pattern, user_input)
        
        if domains:
            domain = domains[0]
            if len(domain) > 20:
                return domain[:17] + "..."
            return domain
        
        return ""
    
    def _get_high_usage_mount(self) -> str:
        """
        Get the mount point with highest disk usage.
        
        Returns:
            Mount point with high usage or empty string
        """
        try:
            result = subprocess.run(['df', '-h'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 5:
                        usage = parts[4].rstrip('%')
                        mount = parts[5]
                        try:
                            usage_num = int(usage)
                            if usage_num > 80:  # High usage threshold
                                return mount
                        except ValueError:
                            continue
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass
        return ""
    
    def get_simple_prompt(self, ai_ready: bool = False) -> str:
        """
        Get a simple prompt without context information (fallback).
        
        Args:
            ai_ready: Whether AI is ready (shows 🤖 emoji)
            
        Returns:
            Simple prompt string
        """
        if ai_ready:
            return "awesh🤖> "
        else:
            return "awesh> "
    
    def update_context(self, **kwargs):
        """
        Update context information manually.
        
        Args:
            **kwargs: Context information to update
        """
        self.current_context.update(kwargs)
    
    def get_context_summary(self) -> str:
        """
        Get a summary of current context for debugging.
        
        Returns:
            Context summary string
        """
        info = self.get_environment_info()
        summary_parts = []
        
        if info['kubectl_context']:
            summary_parts.append(f"K8s: {info['kubectl_context']}")
        if info['kubectl_namespace']:
            summary_parts.append(f"NS: {info['kubectl_namespace']}")
        if info['git_branch']:
            summary_parts.append(f"Git: {info['git_branch']}")
        summary_parts.append(f"Dir: {info['cwd']}")
        
        return " | ".join(summary_parts)
