"""
RepoInvestigator: The Code Detective

This module provides forensic analysis of GitHub repositories using AST parsing,
git history analysis, and structural verification. It operates under strict
forensic protocols to collect objective evidence without opinion.
"""

import ast
import os
import json
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

import git
from git import Repo, GitCommandError
from enum import Enum
from dataclasses import dataclass, field


class GitErrorType(Enum):
    """Enumeration of git operation error types."""
    AUTH_FAILURE = "auth_failure"
    REPO_NOT_FOUND = "repo_not_found"
    EMPTY_REPO = "empty_repo"
    NETWORK_ERROR = "network_error"
    BRANCH_NOT_FOUND = "branch_not_found"
    CLONE_FAILED = "clone_failed"
    UNKNOWN = "unknown"


@dataclass
class GitOperationResult:
    """
    Typed result for git operations with explicit error handling.
    
    Provides clear, typed error results for various git edge cases.
    """
    success: bool
    error_type: Optional[GitErrorType] = None
    error_message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    
    @staticmethod
    def ok(message: str = "", details: Dict[str, Any] = None) -> 'GitOperationResult':
        """Create a successful result."""
        return GitOperationResult(
            success=True,
            error_type=None,
            error_message=message,
            details=details or {}
        )
    
    @staticmethod
    def auth_failure(message: str, details: Dict[str, Any] = None) -> 'GitOperationResult':
        """Create an authentication failure result."""
        return GitOperationResult(
            success=False,
            error_type=GitErrorType.AUTH_FAILURE,
            error_message=message,
            details=details or {}
        )
    
    @staticmethod
    def not_found(message: str, details: Dict[str, Any] = None) -> 'GitOperationResult':
        """Create a repository not found result."""
        return GitOperationResult(
            success=False,
            error_type=GitErrorType.REPO_NOT_FOUND,
            error_message=message,
            details=details or {}
        )
    
    @staticmethod
    def empty_repo(message: str, details: Dict[str, Any] = None) -> 'GitOperationResult':
        """Create an empty repository result."""
        return GitOperationResult(
            success=False,
            error_type=GitErrorType.EMPTY_REPO,
            error_message=message,
            details=details or {}
        )
    
    @staticmethod
    def network_error(message: str, details: Dict[str, Any] = None) -> 'GitOperationResult':
        """Create a network error result."""
        return GitOperationResult(
            success=False,
            error_type=GitErrorType.NETWORK_ERROR,
            error_message=message,
            details=details or {}
        )
    
    @staticmethod
    def branch_not_found(message: str, details: Dict[str, Any] = None) -> 'GitOperationResult':
        """Create a branch not found result."""
        return GitOperationResult(
            success=False,
            error_type=GitErrorType.BRANCH_NOT_FOUND,
            error_message=message,
            details=details or {}
        )
    
    @staticmethod
    def clone_failed(message: str, details: Dict[str, Any] = None) -> 'GitOperationResult':
        """Create a clone failed result."""
        return GitOperationResult(
            success=False,
            error_type=GitErrorType.CLONE_FAILED,
            error_message=message,
            details=details or {}
        )


@dataclass
class GitForensicReport:
    """Structured report of git forensic analysis."""
    commit_count: int = 0
    commits: List[Dict[str, str]] = field(default_factory=list)
    is_atomic: bool = False
    has_stepwise_progression: bool = False
    first_commit_date: Optional[str] = None
    last_commit_date: Optional[str] = None
    analysis: str = ""


@dataclass
class StateManagementReport:
    """Report on state management implementation."""
    has_typed_state: bool = False
    state_location: Optional[str] = None
    uses_pydantic: bool = False
    uses_typed_dict: bool = False
    state_definition: Optional[str] = None
    has_reducers: bool = False
    reducer_types: List[str] = field(default_factory=list)


@dataclass
class GraphOrchestrationReport:
    """Report on LangGraph orchestration."""
    has_stategraph: bool = False
    has_parallel_branches: bool = False
    has_fan_out: bool = False
    has_fan_in: bool = False
    has_conditional_edges: bool = False
    node_definitions: List[str] = field(default_factory=list)
    edge_definitions: List[str] = field(default_factory=list)
    graph_file_location: Optional[str] = None


@dataclass
class SecurityReport:
    """Report on security practices."""
    has_sandboxed_clone: bool = False
    uses_temp_directory: bool = False
    has_error_handling: bool = False
    has_shell_injection_risk: bool = False
    clone_function_code: Optional[str] = None


@dataclass
class StructuredOutputReport:
    """Report on structured output enforcement."""
    uses_with_structured_output: bool = False
    uses_bind_tools: bool = False
    has_pydantic_validation: bool = False
    judge_file_location: Optional[str] = None


class RepoInvestigator:
    """
    The Code Detective - performs forensic analysis of code repositories.
    
    Forensic Protocols:
    - Protocol A: State Structure Verification
    - Protocol B: Graph Wiring Analysis
    - Protocol C: Git Narrative Analysis
    """
    
    def __init__(self, temp_dir: Optional[str] = None):
        self.temp_dir = temp_dir or tempfile.mkdtemp(prefix="audit_")
        self.repo_path: Optional[str] = None
        self.repo: Optional[Repo] = None
        
    def clone_repository(self, url: str) -> Tuple[bool, str]:
        """
        Clone a repository to a sandboxed temporary directory.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Generate unique subdirectory name
            repo_name = url.split("/")[-1].replace(".git", "")
            target_dir = os.path.join(self.temp_dir, repo_name)
            
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
            
            # Clone with error handling
            self.repo = Repo.clone_from(
                url, 
                target_dir,
                depth=50,  # Shallow clone for efficiency
                branch='main'
            )
            
            # Try main branch fallback
            if self.repo is None:
                self.repo = Repo.clone_from(url, target_dir, depth=50)
                
            self.repo_path = target_dir
            return True, f"Successfully cloned to {target_dir}"
            
        except GitCommandError as e:
            # Try alternative branch names
            alt_branches = ['master', 'develop', 'develop']
            for branch in alt_branches:
                try:
                    self.repo = Repo.clone_from(
                        url, 
                        target_dir,
                        depth=50,
                        branch=branch
                    )
                    self.repo_path = target_dir
                    return True, f"Cloned using branch {branch}"
                except:
                    continue
            
            return False, f"Failed to clone: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error during clone: {str(e)}"
    
    def clone_repository_typed(self, url: str) -> GitOperationResult:
        """
        Clone a repository with typed error handling.
        
        Returns:
            GitOperationResult with typed error classification
        """
        try:
            # Generate unique subdirectory name
            repo_name = url.split("/")[-1].replace(".git", "")
            target_dir = os.path.join(self.temp_dir, repo_name)
            
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
            
            # Try main branch first
            try:
                self.repo = Repo.clone_from(
                    url, 
                    target_dir,
                    depth=50,
                    branch='main'
                )
            except GitCommandError as e:
                # Check error type
                error_str = str(e).lower()
                
                # Authentication failure
                if 'authentication' in error_str or 'credential' in error_str or 'unauthorized' in error_str:
                    return GitOperationResult.auth_failure(
                        f"Authentication failed for repository: {url}",
                        {'url': url, 'original_error': str(e)}
                    )
                
                # Repository not found
                if 'not found' in error_str or 'does not exist' in error_str:
                    return GitOperationResult.not_found(
                        f"Repository not found: {url}",
                        {'url': url, 'original_error': str(e)}
                    )
                
                # Network error
                if 'network' in error_str or 'connection' in error_str or 'timeout' in error_str:
                    return GitOperationResult.network_error(
                        f"Network error while cloning: {url}",
                        {'url': url, 'original_error': str(e)}
                    )
                
                # Try alternative branches
                alt_branches = ['master', 'develop', 'main']
                for branch in alt_branches:
                    try:
                        self.repo = Repo.clone_from(
                            url, 
                            target_dir,
                            depth=50,
                            branch=branch
                        )
                        self.repo_path = target_dir
                        return GitOperationResult.ok(
                            f"Successfully cloned using branch {branch}",
                            {'branch': branch, 'path': target_dir}
                        )
                    except GitCommandError:
                        continue
                
                # Branch not found
                return GitOperationResult.branch_not_found(
                    f"Could not find any valid branch (tried: main, master, develop)",
                    {'url': url, 'tried_branches': alt_branches, 'original_error': str(e)}
                )
            
            self.repo_path = target_dir
            return GitOperationResult.ok(
                f"Successfully cloned to {target_dir}",
                {'path': target_dir}
            )
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Determine error type
            if 'authentication' in error_str or 'credential' in error_str:
                return GitOperationResult.auth_failure(str(e), {'original_error': str(e)})
            if 'not found' in error_str or 'does not exist' in error_str:
                return GitOperationResult.not_found(str(e), {'original_error': str(e)})
            if 'network' in error_str or 'connection' in error_str:
                return GitOperationResult.network_error(str(e), {'original_error': str(e)})
            
            return GitOperationResult.clone_failed(str(e), {'original_error': str(e)})
    
    def analyze_git_history(self) -> GitForensicReport:
        """
        Analyze git log for commit patterns.
        
        Success Pattern: >3 commits with progression
        Failure Pattern: Single "init" commit or bulk upload
        """
        report = GitForensicReport()
        
        if not self.repo:
            report.analysis = "No repository loaded"
            return report
            
        try:
            commits = list(self.repo.iter_commits(max_count=100))
            
            # Check for empty repository
            if len(commits) == 0:
                report.commit_count = 0
                report.analysis = "Empty repository - no commits found"
                return report
            
            report.commit_count = len(commits)
            
            for commit in commits:
                report.commits.append({
                    'hash': commit.hexsha[:7],
                    'message': commit.message.strip(),
                    'author': str(commit.author),
                    'date': commit.committed_datetime.isoformat()
                })
            
            if report.commits:
                report.first_commit_date = report.commits[0]['date']
                report.last_commit_date = report.commits[-1]['date']
            
            # Analyze patterns
            if len(commits) <= 1:
                report.is_atomic = False
                report.analysis = "Single commit - monolithic upload detected"
            elif len(commits) <= 3:
                report.is_atomic = False
                report.analysis = f"Only {len(commits)} commits - minimal progression"
            else:
                report.is_atomic = True
                # Check for meaningful progression
                commit_messages = [c['message'].lower() for c in report.commits]
                progress_keywords = ['setup', 'config', 'implement', 'add', 'create', 'fix', 'update']
                has_progress = any(any(kw in msg for kw in progress_keywords) for msg in commit_messages)
                report.has_stepwise_progression = has_progress
                report.analysis = f"Found {len(commits)} commits with {'progression' if has_progress else 'limited progression'}"
                
        except Exception as e:
            report.analysis = f"Error analyzing git history: {str(e)}"
            
        return report
    
    def find_state_definitions(self) -> StateManagementReport:
        """
        Verify the existence and structure of typed state.
        
        Looks for:
        - src/state.py with Pydantic BaseModel or TypedDict
        - src/graph.py with state definitions
        """
        report = StateManagementReport()
        
        if not self.repo_path:
            report.analysis = "No repository path set"
            return report
        
        # Search patterns
        search_paths = [
            os.path.join(self.repo_path, 'src', 'state.py'),
            os.path.join(self.repo_path, 'src', 'graph.py'),
            os.path.join(self.repo_path, 'state.py'),
            os.path.join(self.repo_path, 'graph.py'),
        ]
        
        for path in search_paths:
            if os.path.exists(path):
                report.state_location = path
                try:
                    with open(path, 'utf-8') as f:
                        content = f.read()
                    
                    # Parse AST
                    tree = ast.parse(content)
                    
                    # Check for Pydantic BaseModel
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            # Check for BaseModel inheritance
                            for base in node.bases:
                                if isinstance(base, ast.Name):
                                    if base.id == 'BaseModel':
                                        report.uses_pydantic = True
                                        report.has_typed_state = True
                                    elif base.id == 'TypedDict':
                                        report.uses_typed_dict = True
                                        report.has_typed_state = True
                            
                            # Check for state class name
                            if 'State' in node.name or 'state' in node.name.lower():
                                report.state_definition = ast.get_source_segment(content, node)
                    
                    # Check for reducers
                    if 'operator.add' in content or 'operator.ior' in content:
                        report.has_reducers = True
                        if 'operator.add' in content:
                            report.reducer_types.append('add')
                        if 'operator.ior' in content:
                            report.reducer_types.append('ior')
                            
                except Exception as e:
                    report.analysis = f"Error parsing state file: {str(e)}"
                break
        
        if not report.state_location:
            report.analysis = "No state definition file found"
            
        return report
    
    def analyze_graph_structure(self) -> GraphOrchestrationReport:
        """
        Verify LangGraph StateGraph structure using AST analysis.
        
        Checks for:
        - StateGraph instantiation
        - Parallel branches (fan-out)
        - Synchronization (fan-in)
        - Conditional edges
        """
        report = GraphOrchestrationReport()
        
        if not self.repo_path:
            return report
        
        # Find graph definition files
        graph_files = []
        for root, dirs, files in os.walk(self.repo_path):
            for f in files:
                if f.endswith('.py'):
                    full_path = os.path.join(root, f)
                    try:
                        with open(full_path, 'r', encoding='utf-8') as file:
                            content = file.read()
                            if 'StateGraph' in content or 'graph =' in content:
                                graph_files.append(full_path)
                    except:
                        continue
        
        for graph_file in graph_files:
            try:
                with open(graph_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                # Check for StateGraph
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name):
                            if 'StateGraph' in node.func.id:
                                report.has_stategraph = True
                                report.graph_file_location = graph_file
                
                # Check for parallel patterns
                if 'add_conditional_edges' in content or 'add_edge' in content:
                    # Count unique edge definitions
                    edge_count = content.count('add_edge')
                    conditional_count = content.count('add_conditional_edges')
                    
                    if edge_count > 2:
                        report.has_fan_out = True
                    if edge_count > 3:
                        report.has_fan_in = True
                    if conditional_count > 0:
                        report.has_conditional_edges = True
                
                # Extract node definitions
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Check for node patterns
                        if any(x in node.name.lower() for x in ['node', 'agent', 'detective', 'judge']):
                            report.node_definitions.append(node.name)
                
            except Exception as e:
                report.analysis = f"Error analyzing graph: {str(e)}"
                
        if not report.graph_file_location:
            report.analysis = "No StateGraph definition found"
        
        return report
    
    def check_tool_safety(self) -> SecurityReport:
        """
        Verify safe tool engineering practices.
        
        Checks for:
        - Sandboxed git clone (tempfile)
        - Error handling
        - No shell injection risks
        """
        report = SecurityReport()
        
        if not self.repo_path:
            return report
        
        # Find tool files
        tool_dirs = [
            os.path.join(self.repo_path, 'src', 'tools'),
            os.path.join(self.repo_path, 'tools'),
            self.repo_path,
        ]
        
        for tool_dir in tool_dirs:
            if not os.path.exists(tool_dir):
                continue
                
            for root, dirs, files in os.walk(tool_dir):
                for f in files:
                    if f.endswith('.py'):
                        path = os.path.join(root, f)
                        try:
                            with open(path, 'r', encoding='utf-8') as file:
                                content = file.read()
                            
                            # Check for sandboxing
                            if 'tempfile' in content or 'TemporaryDirectory' in content:
                                report.uses_temp_directory = True
                                report.has_sandboxed_clone = True
                            
                            # Check for error handling
                            if 'try:' in content and 'except' in content:
                                report.has_error_handling = True
                            
                            # Check for shell injection risks
                            if 'os.system' in content or 'subprocess.call' in content:
                                if 'shell=True' in content:
                                    report.has_shell_injection_risk = True
                                else:
                                    # Still check for unsanitized inputs
                                    if 'git clone' in content and 'url' in content:
                                        report.clone_function_code = self._extract_function(content, 'clone')
                            
                        except:
                            continue
        
        if report.has_shell_injection_risk:
            report.analysis = "SECURITY RISK: Shell injection vulnerability detected"
        elif report.has_sandboxed_clone:
            report.analysis = "Safe: Uses temporary directory for cloning"
        else:
            report.analysis = "Warning: No explicit sandboxing found"
            
        return report
    
    def check_structured_output(self) -> StructuredOutputReport:
        """
        Verify judges use structured output enforcement.
        
        Checks for:
        - .with_structured_output() usage
        - .bind_tools() usage
        - Pydantic validation
        """
        report = StructuredOutputReport()
        
        if not self.repo_path:
            return report
        
        # Find judge files
        judge_files = []
        search_paths = [
            os.path.join(self.repo_path, 'src', 'nodes'),
            os.path.join(self.repo_path, 'nodes'),
            self.repo_path,
        ]
        
        for search_path in search_paths:
            if not os.path.exists(search_path):
                continue
            for root, dirs, files in os.walk(search_path):
                for f in files:
                    if 'judge' in f.lower() and f.endswith('.py'):
                        judge_files.append(os.path.join(root, f))
        
        for judge_file in judge_files:
            try:
                with open(judge_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                report.judge_file_location = judge_file
                
                # Check for structured output
                if 'with_structured_output' in content:
                    report.uses_with_structured_output = True
                    report.has_pydantic_validation = True
                if 'bind_tools' in content:
                    report.uses_bind_tools = True
                    report.has_pydantic_validation = True
                    
            except:
                continue
        
        if not report.judge_file_location:
            report.analysis = "No judge implementation files found"
        else:
            report.analysis = f"Found judge file: {report.judge_file_location}"
            
        return report
    
    def _extract_function(self, content: str, func_name: str) -> Optional[str]:
        """Extract a function's code from source content."""
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == func_name:
                    return ast.get_source_segment(content, node)
        except:
            pass
        return None
    
    def cleanup(self):
        """Remove temporary directory."""
        if os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except PermissionError:
                # On Windows, files might be locked - try to at least remove what we can
                import stat
                def handle_remove_readonly(func, path, exc_info):
                    """Clear the readonly bit and reattempt removal."""
                    if not os.access(path, os.W_OK):
                        os.chmod(path, stat.S_IWUSR)
                        func(path)
                try:
                    shutil.rmtree(self.temp_dir, onerror=handle_remove_readonly)
                except:
                    pass  # Best effort cleanup
    
    def run_full_forensic_analysis(self, repo_url: str) -> Dict[str, Any]:
        """
        Run complete forensic analysis on a repository.
        
        Returns:
            Dictionary containing all forensic reports
        """
        # Clone repository
        success, message = self.clone_repository(repo_url)
        if not success:
            return {
                'error': message,
                'clone_success': False
            }
        
        # Run all forensic protocols
        return {
            'clone_success': True,
            'repo_path': self.repo_path,
            'git_forensics': self.analyze_git_history().__dict__,
            'state_management': self.find_state_definitions().__dict__,
            'graph_orchestration': self.analyze_graph_structure().__dict__,
            'security_practices': self.check_tool_safety().__dict__,
            'structured_output': self.check_structured_output().__dict__,
        }
