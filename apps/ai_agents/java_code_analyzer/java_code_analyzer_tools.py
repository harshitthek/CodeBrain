"""
LangChain-based tool definitions.
Wraps existing tools into LangChain Tool objects.
"""

from typing import Optional, Type, List, Dict, Any
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
import re
import os
from .tools import GitTools, AnalyzerAPITools, SourceCodeTools


_COMMIT_HASH_RE = re.compile(r"^[0-9a-fA-F]{7,40}$")


def _sanitize_simple_str(value: Any) -> str:
    """Sanitize simple string arguments.

    Cleans up wrapping quotes and whitespace from tool calls/LLM outputs.
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()
    if value.startswith("```"):
        value = value.strip('`')
    value = value.strip(" \t\r\n\"\'`")
    return value


def _parse_jsonish(value: Any) -> Any:
    """Parse JSON-like arguments.

    Supports dict/list (returns as-is) or str (attempts parsing).
    Parsing order:
    - Standard json.loads
    - json5.loads (supports trailing commas, single quotes, comments)
    Returns sanitized string if parsing fails.
    """
    if isinstance(value, (dict, list)):
        return value
    if value is None:
        return None
    s = _sanitize_simple_str(value)
    if not s:
        return None

    import json
    try:
        return json.loads(s)
    except Exception:
        pass

    try:
        import json5
        return json5.loads(s)
    except Exception:
        return s


def _validate_commit_hash(value: str, field_name: str) -> str:
    """Validate and normalize commit hash argument."""
    v = _sanitize_simple_str(value)
    if not v:
        raise ValueError(f"{field_name} cannot be empty")
    if not _COMMIT_HASH_RE.match(v):
        raise ValueError(f"{field_name} invalid format: '{v}'. Must be a 7-40 character hexadecimal commit hash")
    return v


# ============================================
# Git Tools LangChain Wrappers
# ============================================

class CommitInfoInput(BaseModel):
    """Input for getting commit information"""
    commit_hash: str = Field(description="Commit hash (full or short hash)")


class GetCommitInfoTool(BaseTool):
    """Tool to get commit details"""
    name: str = "get_commit_info"
    description: str = "Get detailed information about a commit, including author, date, message, etc. Use when understanding background of a change."
    args_schema: Type[BaseModel] = CommitInfoInput
    
    git_tools: GitTools = Field(default=None, exclude=True)
    
    def _run(self, commit_hash: str) -> str:
        try:
            commit_hash = _validate_commit_hash(commit_hash, "commit_hash")
        except Exception as e:
            import json
            return json.dumps({
                "error": "Parameter validation failed",
                "tool": "get_commit_info",
                "hint": str(e),
                "received": f"commit_hash='{commit_hash}'"
            }, ensure_ascii=False, indent=2)

        if self._contains_chinese(commit_hash):
            import json
            return json.dumps({
                "error": "Parameter validation failed",
                "tool": "get_commit_info", 
                "hint": "commit_hash parameter cannot contain non-ASCII characters, please check input",
                "received": f"commit_hash='{commit_hash}'"
            }, ensure_ascii=False, indent=2)
            
        result = self.git_tools.get_commit_info(commit_hash)
        import json
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    def _contains_chinese(self, text: str) -> bool:
        """Check if string contains non-ASCII/Chinese characters"""
        if not isinstance(text, str):
            return False
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return True
        return False
    
    async def _arun(self, commit_hash: str) -> str:
        return self._run(commit_hash)


class ChangedFilesInput(BaseModel):
    """Input for getting changed files"""
    base_commit: str = Field(description="Base commit hash")
    new_commit: str = Field(description="Target commit hash")


class GetChangedFilesTool(BaseTool):
    """Tool to get list of changed files"""
    name: str = "get_changed_files"
    description: str = "Get list of files changed between two commits. Use to quickly understand change scope."
    args_schema: Type[BaseModel] = ChangedFilesInput
    
    git_tools: GitTools = Field(default=None, exclude=True)
    
    def _run(self, base_commit: str, new_commit: str) -> str:
        try:
            base_commit = _validate_commit_hash(base_commit, "base_commit")
            new_commit = _validate_commit_hash(new_commit, "new_commit")
        except Exception as e:
            import json
            return json.dumps({
                "error": "Parameter validation failed",
                "tool": "get_changed_files",
                "hint": str(e),
                "received": f"base_commit='{base_commit}', new_commit='{new_commit}'"
            }, ensure_ascii=False, indent=2)

        if self._contains_chinese(base_commit) or self._contains_chinese(new_commit):
            import json
            return json.dumps({
                "error": "Parameter validation failed",
                "tool": "get_changed_files", 
                "hint": "commit hash parameter cannot contain non-ASCII characters, please check input",
                "received": f"base_commit='{base_commit}', new_commit='{new_commit}'"
            }, ensure_ascii=False, indent=2)
            
        result = self.git_tools.get_changed_files(base_commit, new_commit)
        import json
        return json.dumps(result, ensure_ascii=False, indent=2)

    def _contains_chinese(self, text: str) -> bool:
        if not isinstance(text, str):
            return False
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return True
        return False


class GetChangedFilesDetailedTool(BaseTool):
    """Tool to get detailed file changes"""
    name: str = "get_changed_files_detailed"
    description: str = """Get detailed file change information, including change types, line counts, and hunk information.
    
Output format contains:
- path: File path
- changeType: Change type (ADD/MODIFY/DELETE)
- hunks: Changed line blocks containing oldStart, oldLines, newStart, newLines
- additions/deletions: Line statistics

Output can be directly passed to map_hunks_to_symbols for impact analysis."""
    args_schema: Type[BaseModel] = ChangedFilesInput
    
    git_tools: GitTools = Field(default=None, exclude=True)
    
    def _run(self, base_commit: str, new_commit: str) -> str:
        try:
            base_commit = _validate_commit_hash(base_commit, "base_commit")
            new_commit = _validate_commit_hash(new_commit, "new_commit")
        except Exception as e:
            import json
            return json.dumps({
                "error": "Parameter validation failed",
                "tool": "get_changed_files_detailed",
                "hint": str(e),
                "received": f"base_commit='{base_commit}', new_commit='{new_commit}'"
            }, ensure_ascii=False, indent=2)

        if self._contains_chinese(base_commit) or self._contains_chinese(new_commit):
            import json
            return json.dumps({
                "error": "Parameter validation failed",
                "tool": "get_changed_files_detailed", 
                "hint": "commit hash parameter cannot contain non-ASCII characters, please check input",
                "received": f"base_commit='{base_commit}', new_commit='{new_commit}'"
            }, ensure_ascii=False, indent=2)
            
        import json
        result = self.git_tools.get_changed_files_detailed(base_commit, new_commit)
        
        normalized_result = []
        for item in result:
            if "error" in item:
                continue
                
            path = item.get("b_path") or item.get("a_path") or "unknown"
            
            change_type_map = {
                "A": "ADD",
                "D": "DELETE",
                "M": "MODIFY",
                "R": "RENAME"
            }
            change_type = change_type_map.get(item.get("change_type", "M"), "MODIFY")
            
            normalized = {
                "path": path,
                "changeType": change_type,
                "hunks": item.get("hunks", []),
                "additions": item.get("additions", 0),
                "deletions": item.get("deletions", 0)
            }
            
            normalized_result.append(normalized)
        
        return json.dumps(normalized_result, ensure_ascii=False, indent=2)

    def _contains_chinese(self, text: str) -> bool:
        if not isinstance(text, str):
            return False
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return True
        return False


class FileDiffInput(BaseModel):
    """Input for getting file diff"""
    base_commit: str = Field(description="Base commit hash")
    new_commit: str = Field(description="Target commit hash")
    file_path: str = Field(description="File path")
    offset: int = Field(default=0, description="Starting line (0-based) for paginated reading")
    limit: int = Field(default=300, description="Number of lines to read. Default 300")


class GetFileDiffTool(BaseTool):
    """Tool to get file diff"""
    name: str = "get_file_diff"
    description: str = """Get diff content for a specific file between two commits. Supports paginated reading for large diffs.

Important notes:
- Only returns differences (diff) between two versions, not complete file contents.
- Total diff lines != total file lines.
- For small diffs (<300 lines), call directly.
- For large diffs (>300 lines), paginate using offset and limit."""
    args_schema: Type[BaseModel] = FileDiffInput
    
    git_tools: GitTools = Field(default=None, exclude=True)
    
    def _run(self, base_commit: str, new_commit: str, file_path: str, offset: int = 0, limit: int = 300) -> str:
        try:
            base_commit = _validate_commit_hash(base_commit, "base_commit")
            new_commit = _validate_commit_hash(new_commit, "new_commit")
            file_path = _sanitize_simple_str(file_path)
        except Exception as e:
            import json
            return json.dumps({
                "error": "Parameter validation failed",
                "tool": "get_file_diff",
                "hint": str(e),
                "received": f"base_commit='{base_commit}', new_commit='{new_commit}', file_path='{file_path}'"
            }, ensure_ascii=False, indent=2)

        if self._contains_chinese(base_commit) or self._contains_chinese(new_commit) or self._contains_chinese(file_path):
            import json
            return json.dumps({
                "error": "Parameter validation failed",
                "tool": "get_file_diff", 
                "hint": "commit hash and file_path parameters cannot contain non-ASCII characters, please check input",
                "received": f"base_commit='{base_commit}', new_commit='{new_commit}', file_path='{file_path}'"
            }, ensure_ascii=False, indent=2)
            
        return self.git_tools.get_file_diff(base_commit, new_commit, file_path, offset, limit)

    def _contains_chinese(self, text: str) -> bool:
        if not isinstance(text, str):
            return False
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return True
        return False


class FileContentInput(BaseModel):
    """Input for getting file content"""
    commit_hash: str = Field(description="Commit hash")
    file_path: str = Field(description="File path")
    offset: int = Field(default=0, description="Starting line (0-based) for paginated reading")
    limit: int = Field(default=500, description="Number of lines to read. Default 500")


class GetFileContentByCommitTool(BaseTool):
    """Tool to get file content by commit"""
    name: str = "get_file_content_by_commit"
    description: str = """Get content of a file at a specific commit. Supports paginated reading for large files."""
    args_schema: Type[BaseModel] = FileContentInput
    
    git_tools: GitTools = Field(default=None, exclude=True)
    
    def _run(self, commit_hash: str, file_path: str, offset: int = 0, limit: int = 500) -> str:
        try:
            commit_hash = _validate_commit_hash(commit_hash, "commit_hash")
            file_path = _sanitize_simple_str(file_path)
        except Exception as e:
            import json
            return json.dumps({
                "error": "Parameter validation failed",
                "tool": "get_file_content_by_commit",
                "hint": str(e),
                "received": f"commit_hash='{commit_hash}', file_path='{file_path}'"
            }, ensure_ascii=False, indent=2)

        if self._contains_chinese(commit_hash) or self._contains_chinese(file_path):
            import json
            return json.dumps({
                "error": "Parameter validation failed",
                "tool": "get_file_content_by_commit", 
                "hint": "commit hash and file_path parameters cannot contain non-ASCII characters, please check input",
                "received": f"commit_hash='{commit_hash}', file_path='{file_path}'"
            }, ensure_ascii=False, indent=2)
            
        return self.git_tools.get_file_content_by_commit(commit_hash, file_path, offset, limit)

    def _contains_chinese(self, text: str) -> bool:
        if not isinstance(text, str):
            return False
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return True
        return False


class CommitsBetweenInput(BaseModel):
    """Input for getting commit history between two commits"""
    base_commit: str = Field(description="Base commit hash")
    new_commit: str = Field(description="Target commit hash")
    max_count: int = Field(
        default=20, 
        description="Max commits to return. Suggested based on time span: small changes (<1 week): 10-15; medium (1-2 weeks): 20-30; large (>1 month): 50-100"
    )


class GetCommitsBetweenTool(BaseTool):
    """Tool to get commit history between two commits"""
    name: str = "get_commits_between"
    description: str = """Get commit history between two commits. Use to understand the evolution of changes."""
    args_schema: Type[BaseModel] = CommitsBetweenInput
    
    git_tools: GitTools = Field(default=None, exclude=True)
    
    def _run(self, base_commit: str, new_commit: str, max_count: int = 20) -> str:
        try:
            base_commit = _validate_commit_hash(base_commit, "base_commit")
            new_commit = _validate_commit_hash(new_commit, "new_commit")
        except Exception as e:
            import json
            return json.dumps({
                "error": "Parameter validation failed",
                "tool": "get_commits_between",
                "hint": str(e),
                "received": f"base_commit='{base_commit}', new_commit='{new_commit}'"
            }, ensure_ascii=False, indent=2)

        if self._contains_chinese(base_commit) or self._contains_chinese(new_commit):
            import json
            return json.dumps({
                "error": "Parameter validation failed",
                "tool": "get_commits_between", 
                "hint": "commit hash parameter cannot contain non-ASCII characters, please check input",
                "received": f"base_commit='{base_commit}', new_commit='{new_commit}'"
            }, ensure_ascii=False, indent=2)
            
        result = self.git_tools.get_commits_between(base_commit, new_commit, max_count)
        import json
        
        if isinstance(result, list) and len(result) > 0:
            actual_count = len(result)
            first_date = result[0].get('date', '') if result else ''
            last_date = result[-1].get('date', '') if result else ''
            
            meta_info = f"\n\n{'='*70}\n"
            meta_info += f"📊 Fetched {actual_count} commits\n"
            meta_info += f"📅 Time range: {last_date} → {first_date}\n"
            
            if actual_count == max_count:
                meta_info += f"⚠️  Returned count reached limit ({max_count}), more commits may exist\n"
                meta_info += f"💡 To fetch full history, increase max_count:\n"
                meta_info += f"   get_commits_between('{base_commit}', '{new_commit}', max_count={max_count * 2})\n"
            else:
                meta_info += f"✅ Full commit history retrieved\n"
            
            meta_info += f"{'='*70}\n"
            
            return json.dumps(result, ensure_ascii=False, indent=2) + meta_info
        else:
            return json.dumps(result, ensure_ascii=False, indent=2)

    def _contains_chinese(self, text: str) -> bool:
        if not isinstance(text, str):
            return False
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return True
        return False


# ============================================
# Source Code Analysis API Tools LangChain Wrappers
# ============================================

class IndexProjectInput(BaseModel):
    """Input for indexing project"""
    project_id: str = Field(description="Project ID (e.g., education-service), used by backend analyzer to locate local source path")


class IndexProjectTool(BaseTool):
    """Tool to index Java project"""
    name: str = "index_project"
    description: str = "Index Java project and build call graph. This is the prerequisite step before performing any source analysis."
    args_schema: Type[BaseModel] = IndexProjectInput
    
    api_tools: AnalyzerAPITools = Field(default=None, exclude=True)
    
    def _run(self, project_id: str) -> str:
        project_id = _sanitize_simple_str(project_id)
        if self._contains_chinese(project_id):
            import json
            return json.dumps({
                "error": "Parameter validation failed",
                "tool": "index_project", 
                "hint": "project_id parameter cannot contain non-ASCII characters, please check input",
                "received": f"project_id='{project_id}'"
            }, ensure_ascii=False, indent=2)
            
        result = self.api_tools.index_project(project_id)
        import json
        return json.dumps(result, ensure_ascii=False, indent=2)

    def _contains_chinese(self, text: str) -> bool:
        if not isinstance(text, str):
            return False
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return True
        return False


class GetIndexStatusTool(BaseTool):
    """Tool to check index status"""
    name: str = "get_index_status"
    description: str = "Query project index status to verify if indexing is completed."

    args_schema: Type[BaseModel] = IndexProjectInput
    
    api_tools: AnalyzerAPITools = Field(default=None, exclude=True)
    
    def _run(self, project_id: str) -> str:
        project_id = _sanitize_simple_str(project_id)
        result = self.api_tools.get_index_status(project_id)
        import json
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    async def _arun(self, project_id: str) -> str:
        return self._run(project_id)


class MapHunksInput(BaseModel):
    """Input for mapping hunks to symbols"""
    changes: str = Field(
        description="""JSON string of file changes list. Must not contain non-ASCII characters. Each entry must contain:
- path: File path relative to project root
- changeType: Change type (ADD/MODIFY/DELETE/RENAME)
- hunks: List of hunk objects, each containing:
  * oldStart: Old file starting line
  * oldLines: Old file line count
  * newStart: New file starting line
  * newLines: New file line count

Example format:
[{
  "path": "src/main/java/Example.java",
  "changeType": "MODIFY",
  "hunks": [{"oldStart": 10, "oldLines": 5, "newStart": 10, "newLines": 8}]
}]"""
    )
    project_id: str = Field(description="Project ID (e.g. education-service), used by backend analyzer to locate local source path")


class MapHunksToSymbolsTool(BaseTool):
    """Tool to map hunks to symbols"""
    name: str = "map_hunks_to_symbols"
    description: str = """Map file changes to affected specific methods and classes. Used to accurately identify changed code symbols."""
    args_schema: Type[BaseModel] = MapHunksInput
    
    api_tools: AnalyzerAPITools = Field(default=None, exclude=True)
    
    def _run(self, changes: str, project_id: str) -> str:
        import json

        project_id = _sanitize_simple_str(project_id)

        parsed = _parse_jsonish(changes)
        if isinstance(parsed, str):
            error_result = {
                "error": "Parameter parsing failed",
                "tool": "map_hunks_to_symbols",
                "hint": "changes parameter must be valid JSON or JSON5 array. No markdown code blocks or non-ASCII quotes.",
                "original_input": _sanitize_simple_str(changes)[:500] + "..." if len(_sanitize_simple_str(changes)) > 500 else _sanitize_simple_str(changes),
                "suggestion": "Recommend passing the output of get_changed_files_detailed directly as changes input"
            }
            return json.dumps(error_result, ensure_ascii=False, indent=2)

        changes_list = parsed

        if not isinstance(changes_list, list):
            error_result = {
                "error": "Parameter format error",
                "tool": "map_hunks_to_symbols",
                "hint": f"changes parameter must be an array of change objects.\nReceived: {type(changes_list).__name__}",
                "received_value": str(changes_list)[:500] + "..." if len(str(changes_list)) > 500 else str(changes_list)
            }
            return json.dumps(error_result, ensure_ascii=False, indent=2)

        normalized_changes = []
        for idx, change in enumerate(changes_list):
            if not isinstance(change, dict):
                error_result = {
                    "error": "Invalid change item format",
                    "tool": "map_hunks_to_symbols",
                    "hint": f"Change item[{idx}] must be a JSON object.\nReceived: {type(change).__name__}",
                    "received_value": str(change)[:500] + "..." if len(str(change)) > 500 else str(change)
                }
                return json.dumps(error_result, ensure_ascii=False, indent=2)
            
            normalized = {
                "path": change.get("path", ""),
                "changeType": change.get("changeType", "MODIFY"),
                "hunks": []
            }
            
            hunks = change.get("hunks", [])
            for hunk in hunks:
                if isinstance(hunk, dict):
                    if "startLine" in hunk and "endLine" in hunk:
                        start_line = hunk["startLine"]
                        end_line = hunk["endLine"]
                        line_count = max(1, end_line - start_line + 1)
                        normalized_hunk = {
                            "oldStart": start_line,
                            "oldLines": line_count,
                            "newStart": start_line,
                            "newLines": line_count
                        }
                    elif "newStart" in hunk and "newLines" in hunk:
                        normalized_hunk = hunk
                    else:
                        continue
                    
                    normalized["hunks"].append(normalized_hunk)
            
            if not normalized["hunks"]:
                normalized["hunks"].append({
                    "oldStart": 1,
                    "oldLines": 1000,
                    "newStart": 1,
                    "newLines": 1000
                })
            
            normalized_changes.append(normalized)
        
        result = self.api_tools.map_hunks_to_symbols(normalized_changes, project_id)
        return json.dumps(result, ensure_ascii=False, indent=2)


class AnalyzeImpactInput(BaseModel):
    """Input for impact analysis"""
    seeds: str = Field(description="""JSON string of seed methods/classes.
Format: {"methods": [{"fqnClass": "FullClassName", "methodName": "methodName", "paramTypes": ["ParamType"]}], "classes": ["FullClassName"]}
Note: Class names must use fully qualified names (FQN), e.g. 'com.example.MyClass'.
Methods must include fqnClass, methodName, paramTypes.""")
    project_id: str = Field(description="Project ID (e.g. education-service), used by backend analyzer to locate local source path")
    depth: int = Field(default=2, description="Propagation depth, recommended 1-5")
    direction: str = Field(default="both", description="Propagation direction: inbound (callers), outbound (dependencies), both")
    include_edges: bool = Field(default=True, description="Whether to include call edge info")


class AnalyzeImpactTool(BaseTool):
    """Tool for impact analysis"""
    name: str = "analyze_impact"
    description: str = """Analyze impact scope of changes based on call graph propagation to find affected methods.
Important: seeds class names must use fully qualified package names (e.g. com.example.MyClass).
Recommended: use map_hunks_to_symbols first to retrieve affected methods and classes, then pass into this tool."""
    args_schema: Type[BaseModel] = AnalyzeImpactInput

    api_tools: AnalyzerAPITools = Field(default=None, exclude=True)

    def _run(self, seeds: str, project_id: str, depth: int = 2, direction: str = "both", include_edges: bool = True) -> str:
        import json
        project_id = _sanitize_simple_str(project_id)
        seeds_dict = _parse_jsonish(seeds)

        if isinstance(seeds_dict, str):
            return json.dumps({
                "error": "Parameter parsing failed",
                "tool": "analyze_impact",
                "hint": "seeds must be a valid JSON or JSON5 object containing methods/classes. No markdown code blocks.",
                "original_input": _sanitize_simple_str(seeds)[:500] + "..." if len(_sanitize_simple_str(seeds)) > 500 else _sanitize_simple_str(seeds),
                "suggestion": "Recommend constructing seeds from map_hunks_to_symbols output before calling"
            }, ensure_ascii=False, indent=2)

        if isinstance(seeds_dict, dict):
            self._validate_seeds(seeds_dict)

        try:
            result = self.api_tools.analyze_impact(seeds_dict, project_id, depth, direction, include_edges)
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            error_msg = str(e)
            if "400" in error_msg:
                hint = "API returned 400 error, likely parameter formatting issue. Check:\n1. Class name contains invalid characters\n2. JSON format is valid\n3. Required fields present\n4. Use map_hunks_to_symbols first"
                return json.dumps({
                    "error": error_msg,
                    "hint": hint,
                    "original_params": f"project_id={project_id}, depth={depth}, direction={direction}"
                }, ensure_ascii=False, indent=2)
            else:
                raise

    def _validate_seeds(self, seeds_dict: dict) -> None:
        """Validate seeds parameter structure"""
        errors = []

        methods = seeds_dict.get("methods", [])
        if methods:
            for idx, method in enumerate(methods):
                if not isinstance(method, dict):
                    errors.append(f"methods[{idx}] must be an object")
                    continue

                fqn_class = method.get("fqnClass", "")
                if fqn_class and not self._is_valid_java_class_name(fqn_class):
                    errors.append(f"methods[{idx}].fqnClass invalid format: '{fqn_class}'. Java class name must contain only letters, numbers, underscores, dots, and angle brackets")

                method_name = method.get("methodName", "")
                if method_name and not self._is_valid_method_name(method_name):
                    errors.append(f"methods[{idx}].methodName invalid format: '{method_name}'. Method name must contain only letters, numbers, and underscores")

                param_types = method.get("paramTypes", [])
                if isinstance(param_types, list):
                    for pidx, param_type in enumerate(param_types):
                        if isinstance(param_type, str) and not self._is_valid_java_type(param_type):
                            errors.append(f"methods[{idx}].paramTypes[{pidx}] invalid format: '{param_type}'")

        classes = seeds_dict.get("classes", [])
        if classes:
            for idx, cls in enumerate(classes):
                if not self._is_valid_java_class_name(cls):
                    errors.append(f"classes[{idx}] invalid format: '{cls}'")

        if errors:
            error_msg = "\n".join(errors)
            raise ValueError(f"Parameter validation failed:\n{error_msg}\n\nPlease rebuild parameters ensuring:\n1. Fully qualified class names (e.g. com.example.MyClass)\n2. No non-ASCII characters\n3. paramTypes is array format\n4. Use map_hunks_to_symbols for seed methods")

    def _is_valid_java_class_name(self, name: str) -> bool:
        if not name or not isinstance(name, str):
            return False
        pattern = r'^[a-zA-Z0-9_<>,.]+$'
        return re.match(pattern, name) is not None

    def _is_valid_method_name(self, name: str) -> bool:
        if not name or not isinstance(name, str):
            return False
        pattern = r'^[a-zA-Z0-9_]+$'
        return re.match(pattern, name) is not None

    def _is_valid_java_type(self, type_str: str) -> bool:
        if not type_str or not isinstance(type_str, str):
            return False
        pattern = r'^[a-zA-Z0-9_<?>,.]+$'
        return re.match(pattern, type_str) is not None


# ============================================
# Source Code Reading Tools LangChain Wrappers
# ============================================

class ReadFileInput(BaseModel):
    """Input for reading file"""
    relative_path: str = Field(description="File path relative to project root")
    max_lines: int = Field(default=500, description="Max lines to read per call, default 500")
    offset: int = Field(default=0, description="Starting line (0-based) for paginated reading")


class ReadFileTool(BaseTool):
    """Tool to read file"""
    name: str = "read_file"
    description: str = """Read content of a file in the project. Supports paginated reading for large files.
Important restrictions:
- Can only read files, cannot read directories (use list_directory instead)
- To find files, use find_file tool"""
    args_schema: Type[BaseModel] = ReadFileInput
    
    source_tools: SourceCodeTools = Field(default=None, exclude=True)
    
    def _run(self, relative_path: str, max_lines: int = 500, offset: int = 0) -> str:
        relative_path = _sanitize_simple_str(relative_path)
        if self._contains_chinese(relative_path):
            import json
            return json.dumps({
                "error": "Parameter validation failed",
                "tool": "read_file", 
                "hint": "relative_path parameter cannot contain non-ASCII characters, please check input",
                "received": f"relative_path='{relative_path}'"
            }, ensure_ascii=False, indent=2)
            
        result = self.source_tools.read_file(relative_path, max_lines, offset)
        return result

    def _contains_chinese(self, text: str) -> bool:
        if not isinstance(text, str):
            return False
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return True
        return False


class SearchInFileInput(BaseModel):
    """Input for searching within file"""
    relative_path: str = Field(description="File path")
    keyword: str = Field(description="Search keyword")


class SearchInFileTool(BaseTool):
    """Tool to search within file"""
    name: str = "search_in_file"
    description: str = """Search keyword inside file content.
Note: searches file contents, not filenames (use find_file for filenames)."""
    args_schema: Type[BaseModel] = SearchInFileInput
    
    source_tools: SourceCodeTools = Field(default=None, exclude=True)
    
    def _run(self, relative_path: str, keyword: str) -> str:
        relative_path = _sanitize_simple_str(relative_path)
        keyword = _sanitize_simple_str(keyword)
        if self._contains_chinese(relative_path) or self._contains_chinese(keyword):
            import json
            return json.dumps({
                "error": "Parameter validation failed",
                "tool": "search_in_file", 
                "hint": "relative_path and keyword parameters cannot contain non-ASCII characters, please check input",
                "received": f"relative_path='{relative_path}', keyword='{keyword}'"
            }, ensure_ascii=False, indent=2)
            
        result = self.source_tools.search_in_file(relative_path, keyword)
        import json
        return json.dumps(result, ensure_ascii=False, indent=2)

    def _contains_chinese(self, text: str) -> bool:
        if not isinstance(text, str):
            return False
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return True
        return False


class ListJavaFilesInput(BaseModel):
    """Input for listing Java files"""
    directory: str = Field(default="", description="Relative directory path, empty string indicates project root")


class ListJavaFilesTool(BaseTool):
    """Tool to list Java files"""
    name: str = "list_java_files"
    description: str = "List all Java files under a directory. Returns statistics grouped by directory and full file list."
    args_schema: Type[BaseModel] = ListJavaFilesInput
    
    source_tools: SourceCodeTools = Field(default=None, exclude=True)
    
    def _run(self, directory: str = "") -> str:
        directory = _sanitize_simple_str(directory)
        if self._contains_chinese(directory):
            import json
            return json.dumps({
                "error": "Parameter validation failed",
                "tool": "list_java_files", 
                "hint": "directory parameter cannot contain non-ASCII characters, please check input",
                "received": f"directory='{directory}'"
            }, ensure_ascii=False, indent=2)
            
        result = self.source_tools.list_java_files(directory)
        import json
        from collections import defaultdict
        
        dir_stats = defaultdict(list)
        for file_path in result:
            if isinstance(file_path, str) and not file_path.startswith("Error"):
                parts = file_path.split('/')
                if len(parts) > 1:
                    dir_path = '/'.join(parts[:-1])
                    dir_stats[dir_path].append(parts[-1])
                else:
                    dir_stats['root'].append(file_path)
        
        output = {
            "total": len(result),
            "directory_stats": {
                dir_path: {
                    "file_count": len(files),
                    "file_list": sorted(files)
                }
                for dir_path, files in sorted(dir_stats.items())
            }
        }
        
        return json.dumps(output, ensure_ascii=False, indent=2)

    def _contains_chinese(self, text: str) -> bool:
        if not isinstance(text, str):
            return False
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return True
        return False


class ListDirectoryInput(BaseModel):
    """Input for listing directory contents"""
    directory: str = Field(default="", description="Relative directory path, empty string indicates project root")


class ListDirectoryTool(BaseTool):
    """Tool to list directory contents"""
    name: str = "list_directory"
    description: str = """List files and subdirectories under specified directory. Only lists direct children, non-recursive."""
    args_schema: Type[BaseModel] = ListDirectoryInput
    
    source_tools: SourceCodeTools = Field(default=None, exclude=True)
    
    def _run(self, directory: str = "") -> str:
        if self._contains_chinese(directory):
            import json
            return json.dumps({
                "error": "Parameter validation failed",
                "tool": "list_directory", 
                "hint": "directory parameter cannot contain non-ASCII characters, please check input",
                "received": f"directory='{directory}'"
            }, ensure_ascii=False, indent=2)
            
        result = self.source_tools.list_directory(directory)
        import json
        return json.dumps(result, ensure_ascii=False, indent=2)

    def _contains_chinese(self, text: str) -> bool:
        if not isinstance(text, str):
            return False
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return True
        return False


class FindFileInput(BaseModel):
    """Input for finding files"""
    pattern: str = Field(description="Filename pattern supporting wildcards, e.g. 'pom.xml', '*.xml', '**/*.properties'")
    max_results: int = Field(default=200, description="Max results to return, default 200")


class FindFileTool(BaseTool):
    """Tool to find files"""
    name: str = "find_file"
    description: str = """Find specific filenames in project. Supports wildcards * and ?."""
    args_schema: Type[BaseModel] = FindFileInput
    
    source_tools: SourceCodeTools = Field(default=None, exclude=True)
    
    def _run(self, pattern: str, max_results: int = 200) -> str:
        if self._contains_chinese(pattern):
            import json
            return json.dumps({
                "error": "Parameter validation failed",
                "tool": "find_file", 
                "hint": "pattern parameter cannot contain non-ASCII characters, please check input",
                "received": f"pattern='{pattern}'"
            }, ensure_ascii=False, indent=2)
            
        result = self.source_tools.find_file(pattern, max_results)
        import json
        return json.dumps(result, ensure_ascii=False, indent=2)

    def _contains_chinese(self, text: str) -> bool:
        if not isinstance(text, str):
            return False
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return True
        return False


# ============================================
# Tool Factory Function
# ============================================

def create_langchain_tools(repo_path: str, java_analyzer_service_url: str, project_id: str = None) -> List[BaseTool]:
    """
    Create all LangChain tools.
    
    Args:
        repo_path: Project repository path
        java_analyzer_service_url: Java source code analyzer service URL
        project_id: Project ID (optional, inferred from repo_path if not provided)
        
    Returns:
        List of tools
    """
    from .tools import get_all_tools
    
    if project_id is None:
        try:
            from django.conf import settings
            project_mapping = getattr(settings, 'PROJECT_ID_REPO_MAPPING', {})
            base_dir = getattr(settings, 'JAVA_PROJECTS_BASE_DIR', '/home')
            
            for pid in project_mapping.keys():
                expected_path = os.path.join(base_dir, pid)
                if repo_path == expected_path or repo_path.startswith(expected_path):
                    project_id = pid
                    break
            else:
                project_id = os.path.basename(repo_path.rstrip('/'))
        except Exception:
            project_id = os.path.basename(repo_path.rstrip('/'))
    
    tools_instances = get_all_tools(repo_path, java_analyzer_service_url)
    git = tools_instances["git"]
    api = tools_instances["api"]
    source = tools_instances["source"]
    
    tools = [
        # Git Tools
        GetCommitInfoTool(git_tools=git),
        GetChangedFilesTool(git_tools=git),
        GetChangedFilesDetailedTool(git_tools=git),
        GetFileDiffTool(git_tools=git),
        GetFileContentByCommitTool(git_tools=git),
        GetCommitsBetweenTool(git_tools=git),
        
        # API Tools
        IndexProjectTool(api_tools=api),
        GetIndexStatusTool(api_tools=api),
        MapHunksToSymbolsTool(api_tools=api),
        AnalyzeImpactTool(api_tools=api),
        
        # Source Tools
        ReadFileTool(source_tools=source),
        SearchInFileTool(source_tools=source),
        ListJavaFilesTool(source_tools=source),
        ListDirectoryTool(source_tools=source),
        FindFileTool(source_tools=source),
    ]
    
    return tools
