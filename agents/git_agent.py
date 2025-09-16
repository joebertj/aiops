"""
Git MCP Agent - AI-powered Git operations
Handles repository management, commits, branches, and workflow optimization
"""

import subprocess
import json
import os
from typing import Dict, List, Optional, Any
from .base_agent import BaseAgent


class GitAgent(BaseAgent):
    """Git MCP Agent for AI-assisted Git operations"""
    
    def __init__(self):
        super().__init__("git")
        self.supported_commands = [
            "git_status", "git_log", "git_diff", "git_add", "git_commit",
            "git_branch", "git_checkout", "git_merge", "git_rebase",
            "git_push", "git_pull", "git_fetch", "git_remote",
            "git_reset", "git_revert", "git_stash", "git_blame"
        ]
    
    def execute(self, command: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Git MCP command"""
        try:
            if command == "git_status":
                return self._git_status(args)
            elif command == "git_log":
                return self._git_log(args)
            elif command == "git_diff":
                return self._git_diff(args)
            elif command == "git_add":
                return self._git_add(args)
            elif command == "git_commit":
                return self._git_commit(args)
            elif command == "git_branch":
                return self._git_branch(args)
            elif command == "git_checkout":
                return self._git_checkout(args)
            elif command == "git_merge":
                return self._git_merge(args)
            elif command == "git_rebase":
                return self._git_rebase(args)
            elif command == "git_push":
                return self._git_push(args)
            elif command == "git_pull":
                return self._git_pull(args)
            elif command == "git_fetch":
                return self._git_fetch(args)
            elif command == "git_remote":
                return self._git_remote(args)
            elif command == "git_reset":
                return self._git_reset(args)
            elif command == "git_revert":
                return self._git_revert(args)
            elif command == "git_stash":
                return self._git_stash(args)
            elif command == "git_blame":
                return self._git_blame(args)
            else:
                return {"error": f"Unsupported Git command: {command}"}
        except Exception as e:
            return {"error": f"Git operation failed: {str(e)}"}
    
    def _run_git_command(self, git_args: List[str], cwd: Optional[str] = None) -> Dict[str, Any]:
        """Run git command and return structured result"""
        try:
            if cwd is None:
                cwd = os.getcwd()
            
            result = subprocess.run(
                ["git"] + git_args,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"error": "Git command timed out"}
        except Exception as e:
            return {"error": f"Git command failed: {str(e)}"}
    
    def _git_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get repository status"""
        git_args = ["status", "--porcelain"]
        if args.get("verbose", False):
            git_args = ["status"]
        
        result = self._run_git_command(git_args)
        if result.get("success"):
            # Parse porcelain output for structured data
            files = []
            for line in result["stdout"].strip().split('\n'):
                if line:
                    status = line[:2]
                    filename = line[3:]
                    files.append({
                        "status": status,
                        "filename": filename,
                        "staged": status[0] != ' ',
                        "modified": status[1] != ' '
                    })
            
            result["files"] = files
            result["summary"] = {
                "total_files": len(files),
                "staged_files": len([f for f in files if f["staged"]]),
                "modified_files": len([f for f in files if f["modified"]])
            }
        
        return result
    
    def _git_log(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get commit history"""
        git_args = ["log", "--oneline", "--graph"]
        
        if args.get("limit"):
            git_args.extend(["-n", str(args["limit"])])
        
        if args.get("author"):
            git_args.extend(["--author", args["author"]])
        
        if args.get("since"):
            git_args.extend(["--since", args["since"]])
        
        if args.get("file"):
            git_args.extend(["--", args["file"]])
        
        result = self._run_git_command(git_args)
        if result.get("success"):
            # Parse log entries
            commits = []
            for line in result["stdout"].strip().split('\n'):
                if line and not line.startswith('*') and not line.startswith('|'):
                    parts = line.split(' ', 1)
                    if len(parts) == 2:
                        commits.append({
                            "hash": parts[0],
                            "message": parts[1]
                        })
            
            result["commits"] = commits
        
        return result
    
    def _git_diff(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get diff information"""
        git_args = ["diff"]
        
        if args.get("staged", False):
            git_args.append("--cached")
        
        if args.get("file"):
            git_args.extend(["--", args["file"]])
        
        result = self._run_git_command(git_args)
        return result
    
    def _git_add(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Stage files"""
        git_args = ["add"]
        
        if args.get("all", False):
            git_args.append("--all")
        elif args.get("file"):
            git_args.append(args["file"])
        else:
            git_args.append(".")
        
        return self._run_git_command(git_args)
    
    def _git_commit(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create commit"""
        git_args = ["commit"]
        
        if args.get("message"):
            git_args.extend(["-m", args["message"]])
        
        if args.get("amend", False):
            git_args.append("--amend")
        
        if args.get("no_edit", False):
            git_args.append("--no-edit")
        
        result = self._run_git_command(git_args)
        return result
    
    def _git_branch(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Branch operations"""
        git_args = ["branch"]
        
        if args.get("list", True):
            git_args.append("-a")  # List all branches
        elif args.get("create"):
            git_args.extend(["-b", args["create"]])
        elif args.get("delete"):
            git_args.extend(["-d", args["delete"]])
        
        result = self._run_git_command(git_args)
        if result.get("success") and args.get("list", True):
            # Parse branch list
            branches = []
            current_branch = None
            
            for line in result["stdout"].strip().split('\n'):
                if line:
                    if line.startswith('*'):
                        current_branch = line[2:].strip()
                        branches.append({
                            "name": current_branch,
                            "current": True,
                            "remote": False
                        })
                    else:
                        branch_name = line.strip()
                        is_remote = branch_name.startswith('remotes/')
                        branches.append({
                            "name": branch_name,
                            "current": False,
                            "remote": is_remote
                        })
            
            result["branches"] = branches
            result["current_branch"] = current_branch
        
        return result
    
    def _git_checkout(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Switch branches or restore files"""
        git_args = ["checkout"]
        
        if args.get("branch"):
            git_args.append(args["branch"])
        elif args.get("file"):
            git_args.extend(["--", args["file"]])
        
        return self._run_git_command(git_args)
    
    def _git_merge(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Merge branches"""
        git_args = ["merge"]
        
        if args.get("branch"):
            git_args.append(args["branch"])
        
        if args.get("no_ff", False):
            git_args.append("--no-ff")
        
        if args.get("squash", False):
            git_args.append("--squash")
        
        return self._run_git_command(git_args)
    
    def _git_rebase(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Rebase operations"""
        git_args = ["rebase"]
        
        if args.get("branch"):
            git_args.append(args["branch"])
        elif args.get("continue", False):
            git_args.append("--continue")
        elif args.get("abort", False):
            git_args.append("--abort")
        
        return self._run_git_command(git_args)
    
    def _git_push(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Push to remote"""
        git_args = ["push"]
        
        if args.get("remote"):
            git_args.append(args["remote"])
        
        if args.get("branch"):
            git_args.append(args["branch"])
        
        if args.get("force", False):
            git_args.append("--force")
        
        return self._run_git_command(git_args)
    
    def _git_pull(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Pull from remote"""
        git_args = ["pull"]
        
        if args.get("remote"):
            git_args.append(args["remote"])
        
        if args.get("branch"):
            git_args.append(args["branch"])
        
        return self._run_git_command(git_args)
    
    def _git_fetch(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch from remote"""
        git_args = ["fetch"]
        
        if args.get("remote"):
            git_args.append(args["remote"])
        
        return self._run_git_command(git_args)
    
    def _git_remote(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Remote operations"""
        git_args = ["remote"]
        
        if args.get("list", True):
            git_args.append("-v")
        elif args.get("add"):
            git_args.extend(["add", args["add"]["name"], args["add"]["url"]])
        elif args.get("remove"):
            git_args.extend(["remove", args["remove"]])
        
        result = self._run_git_command(git_args)
        if result.get("success") and args.get("list", True):
            # Parse remote list
            remotes = []
            for line in result["stdout"].strip().split('\n'):
                if line:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        remotes.append({
                            "name": parts[0],
                            "url": parts[1],
                            "fetch": parts[2] if len(parts) > 2 else None
                        })
            
            result["remotes"] = remotes
        
        return result
    
    def _git_reset(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Reset operations"""
        git_args = ["reset"]
        
        if args.get("mode", "mixed") == "soft":
            git_args.append("--soft")
        elif args.get("mode", "mixed") == "hard":
            git_args.append("--hard")
        
        if args.get("commit"):
            git_args.append(args["commit"])
        
        return self._run_git_command(git_args)
    
    def _git_revert(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Revert commits"""
        git_args = ["revert"]
        
        if args.get("commit"):
            git_args.append(args["commit"])
        
        if args.get("no_edit", False):
            git_args.append("--no-edit")
        
        return self._run_git_command(git_args)
    
    def _git_stash(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Stash operations"""
        git_args = ["stash"]
        
        if args.get("save"):
            git_args.extend(["save", args["save"]])
        elif args.get("pop", False):
            git_args.append("pop")
        elif args.get("list", True):
            git_args.append("list")
        elif args.get("drop", False):
            git_args.append("drop")
        
        result = self._run_git_command(git_args)
        if result.get("success") and args.get("list", True):
            # Parse stash list
            stashes = []
            for line in result["stdout"].strip().split('\n'):
                if line:
                    parts = line.split(':', 2)
                    if len(parts) >= 3:
                        stashes.append({
                            "stash": parts[0],
                            "branch": parts[1],
                            "message": parts[2]
                        })
            
            result["stashes"] = stashes
        
        return result
    
    def _git_blame(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Blame file lines"""
        git_args = ["blame"]
        
        if args.get("file"):
            git_args.append(args["file"])
        else:
            return {"error": "File required for blame operation"}
        
        result = self._run_git_command(git_args)
        if result.get("success"):
            # Parse blame output
            lines = []
            for line in result["stdout"].strip().split('\n'):
                if line:
                    parts = line.split('\t', 2)
                    if len(parts) >= 3:
                        commit_info = parts[0].split()
                        lines.append({
                            "commit": commit_info[0],
                            "author": commit_info[1],
                            "date": commit_info[2],
                            "line_number": commit_info[3],
                            "content": parts[2]
                        })
            
            result["lines"] = lines
        
        return result
