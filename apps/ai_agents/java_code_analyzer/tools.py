"""
Tool functions collection: Tools for autonomous invocation by LLM.
Includes Git extraction tools and source code analysis REST API tools.
"""

from typing import List, Dict, Any, Optional, Tuple
import subprocess
from git import Repo
import requests
from pathlib import Path


def _paginate_lines(
    lines: List[str],
    offset: int,
    limit: int,
    file_path: str,
    content_type: str = "File"
) -> Tuple[str, str]:
    """
    Common helper for line pagination.
    
    Args:
        lines: List of all lines
        offset: Starting line index (0-based)
        limit: Max lines to read
        file_path: File path (for meta display)
        content_type: Content type description (e.g. "File", "Diff")
        
    Returns:
        Tuple of (chunk content, metadata)
    """
    total_lines = len(lines)
    
    # Check if offset is out of range
    if offset >= total_lines:
        meta_info = f"\n{'='*70}\n"
        meta_info += f"📄 File: {file_path}\n"
        meta_info += f"📊 Total {content_type} lines: {total_lines} lines\n"
        meta_info += f"❌ Error: offset ({offset}) out of range (Total lines: {total_lines})\n"
        meta_info += f"💡 Tip: offset should be between 0 and {total_lines - 1}\n"
        meta_info += f"{'='*70}\n"
        return "", meta_info
    
    # Slice content
    end = min(offset + limit, total_lines)
    selected_lines = lines[offset:end]
    content = '\n'.join(selected_lines)
    
    # Append metadata
    meta_info = f"\n{'='*70}\n"
    meta_info += f"📄 File: {file_path}\n"
    meta_info += f"📊 Total {content_type} lines: {total_lines} lines\n"
    meta_info += f"📍 Current read range: lines {offset + 1} - {end}\n"
    
    if end < total_lines:
        remaining = total_lines - end
        meta_info += f"⚠️  {remaining} lines unread\n"
        meta_info += f"💡 To continue reading, use: offset={end}, limit={limit}\n"
    else:
        meta_info += f"✅ Read complete content\n"
    
    meta_info += f"{'='*70}\n"
    
    return content, meta_info


class GitTools:
    """Git tools"""
    
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.repo = Repo(repo_path)
    
    def pull_latest(self, remote: str = "origin", branch: Optional[str] = None, allow_dirty: bool = True):
        """
        Pull latest code
        
        Args:
            remote: Remote repository name
            branch: Branch to pull
            allow_dirty: Whether uncommitted changes are allowed
        """
        if self.repo.is_dirty(untracked_files=True) and not allow_dirty:
            raise RuntimeError("Repository has uncommitted changes, aborting automatic pull")
        remote_obj = self.repo.remotes[remote]
        remote_obj.fetch()
        if self.repo.head.is_detached and branch is None:
            raise RuntimeError("Currently in detached HEAD state, must explicitly specify branch to pull")
        target_branch = branch or self.repo.active_branch.name
        remote_obj.pull(target_branch)
    
    def get_commit_info(self, commit_hash: str) -> Dict[str, Any]:
        """
        Get basic commit information.
        
        Args:
            commit_hash: Commit hash
            
        Returns:
            Dictionary containing commit information
        """
        try:
            commit = self.repo.commit(commit_hash)
            return {
                "hash": commit.hexsha,
                "short_hash": commit.hexsha[:8],
                "author": str(commit.author),
                "email": commit.author.email,
                "date": commit.committed_datetime.isoformat(),
                "message": commit.message.strip(),
                "summary": commit.summary,
                "parents": [p.hexsha for p in commit.parents]
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_changed_files(self, base_commit: str, new_commit: str) -> List[str]:
        """
        Get list of changed files between two commits.
        
        Args:
            base_commit: Base commit
            new_commit: Target commit
            
        Returns:
            List of changed file paths
        """
        try:
            base = self.repo.commit(base_commit)
            new = self.repo.commit(new_commit)
            
            diff_index = base.diff(new)
            files = []
            
            for diff in diff_index:
                if diff.a_path:
                    files.append(diff.a_path)
                if diff.b_path and diff.b_path != diff.a_path:
                    files.append(diff.b_path)
            
            return list(set(files))
        except Exception as e:
            return [f"Error: {e}"]
    
    def get_changed_files_detailed(self, base_commit: str, new_commit: str) -> List[Dict[str, Any]]:
        """
        Get detailed file change information, including change type, line statistics, and hunk info.
        
        Args:
            base_commit: Base commit
            new_commit: Target commit
            
        Returns:
            List of detailed changes with path, changeType, hunks
        """
        try:
            base = self.repo.commit(base_commit)
            new = self.repo.commit(new_commit)
            
            diff_index = base.diff(new, create_patch=True)
            changes = []
            
            for diff in diff_index:
                change_info = {
                    "a_path": diff.a_path,
                    "b_path": diff.b_path,
                    "change_type": self._get_change_type(diff),
                    "renamed": diff.renamed,
                    "deleted": diff.deleted_file,
                    "new_file": diff.new_file,
                }
                
                hunks = []
                if diff.diff:
                    try:
                        diff_text = diff.diff.decode('utf-8', errors='ignore')
                        additions = diff_text.count('\n+') - diff_text.count('\n+++')
                        deletions = diff_text.count('\n-') - diff_text.count('\n---')
                        change_info["additions"] = additions
                        change_info["deletions"] = deletions
                        
                        import re
                        hunk_pattern = r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@'
                        for match in re.finditer(hunk_pattern, diff_text):
                            old_start = int(match.group(1))
                            old_lines = int(match.group(2)) if match.group(2) else 1
                            new_start = int(match.group(3))
                            new_lines = int(match.group(4)) if match.group(4) else 1
                            
                            hunks.append({
                                "oldStart": old_start,
                                "oldLines": old_lines,
                                "newStart": new_start,
                                "newLines": new_lines
                            })
                    except:
                        pass
                
                change_info["hunks"] = hunks
                changes.append(change_info)
            
            return changes
        except Exception as e:
            return [{"error": str(e)}]
    
    def get_file_diff(
        self, 
        base_commit: str, 
        new_commit: str, 
        file_path: str,
        offset: int = 0,
        limit: int = 300
    ) -> str:
        """
        Get detailed diff for a specific file. Supports paginated reading for large diffs.
        
        Args:
            base_commit: Base commit
            new_commit: Target commit
            file_path: File path
            offset: Starting line (0-based)
            limit: Max lines to read
            
        Returns:
            Diff text with metadata
        """
        try:
            result = subprocess.run(
                ['git', 'diff', f'{base_commit}..{new_commit}', '--', file_path],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            full_diff = result.stdout
            
            lines = full_diff.split('\n')
            content, meta_info = _paginate_lines(lines, offset, limit, file_path, "Diff")
            
            return content + meta_info
        except Exception as e:
            return f"Error: {e}"
    
    def get_file_content_by_commit(
        self, 
        commit_hash: str, 
        file_path: str,
        offset: int = 0,
        limit: int = 500
    ) -> str:
        """
        Get file content at a specific commit. Supports paginated reading for large files.
        
        Args:
            commit_hash: Commit hash
            file_path: File path
            offset: Starting line (0-based)
            limit: Max lines to read
            
        Returns:
            File content with metadata
        """
        try:
            commit = self.repo.commit(commit_hash)
            blob = commit.tree / file_path
            full_content = blob.data_stream.read().decode('utf-8', errors='ignore')
            
            lines = full_content.split('\n')
            content, meta_info = _paginate_lines(lines, offset, limit, file_path, "File")
            
            return content + meta_info
        except Exception as e:
            return f"Error: {e}"
    
    def get_commits_between(self, base_commit: str, new_commit: str, max_count: int = 20) -> List[Dict[str, Any]]:
        """
        Get list of commits between two commits.
        
        Args:
            base_commit: Base commit
            new_commit: Target commit
            max_count: Max commits to return
            
        Returns:
            List of commit information dictionaries
        """
        try:
            commits = list(self.repo.iter_commits(f'{base_commit}..{new_commit}', max_count=max_count))
            return [
                {
                    "hash": c.hexsha[:8],
                    "author": str(c.author),
                    "date": c.committed_datetime.isoformat(),
                    "message": c.summary
                }
                for c in commits
            ]
        except Exception as e:
            return [{"error": str(e)}]
    
    def get_file_history(self, file_path: str, max_count: int = 10) -> List[Dict[str, Any]]:
        """
        Get modification history for a file.
        
        Args:
            file_path: File path
            max_count: Max history records to return
            
        Returns:
            List of history commits
        """
        try:
            commits = list(self.repo.iter_commits(paths=file_path, max_count=max_count))
            return [
                {
                    "hash": c.hexsha[:8],
                    "author": str(c.author),
                    "date": c.committed_datetime.isoformat(),
                    "message": c.summary
                }
                for c in commits
            ]
        except Exception as e:
            return [{"error": str(e)}]
    
    def _get_change_type(self, diff) -> str:
        """Determine change type"""
        if diff.new_file:
            return "ADD"
        elif diff.deleted_file:
            return "DELETE"
        elif diff.renamed:
            return "RENAME"
        else:
            return "MODIFY"
    
    def get_current_ref(self) -> str:
        """
        Get current Git ref.
        
        Returns:
            Branch name (e.g. "main") or commit hash (detached HEAD)
        """
        if self.repo.head.is_detached:
            return self.repo.head.commit.hexsha
        else:
            return self.repo.active_branch.name

    def checkout_version(self, ref: str):
        """
        Checkout specified version.
        
        Args:
            ref: Version ref (commit hash or branch name)
        """
        self.repo.git.checkout(ref)


class AnalyzerAPITools:
    """Source code analysis REST API tools"""
    
    def __init__(self, base_url: str = "http://localhost:8089"):
        self.base_url = base_url.rstrip("/")
    
    def index_project(self, project_id: str) -> Dict[str, Any]:
        """
        Index project and build call graph.
        
        Args:
            project_id: Target Java project ID, used by analyzer service to locate source code
            
        Returns:
            Index status
        """
        try:
            url = f"{self.base_url}/index/project?projectId={project_id}"
            payload = {
                "sourceSets": ["main"],
                "maven": {"resolveDeps": True},
                "jdkHome": None
            }
            print(f"\n🌐 API Call: POST {url}")
            print(f"📦 Project ID: {project_id}")
            print(f"📦 Request Body: {payload}")
            print(f"🔍 Full URL: {url}")
            print(f"📊 Details: projectId={project_id}, sourceSets=main, maven.resolveDeps=True")
            
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            print(f"✅ Success: {result}")
            return result
        except Exception as e:
            print(f"❌ Call Failed: {str(e)}")
            return {"error": str(e)}
    
    def get_index_status(self, project_id: str) -> Dict[str, Any]:
        """
        Get indexing status.
        
        Args:
            project_id: Project ID
            
        Returns:
            Index status information
        """
        try:
            url = f"{self.base_url}/index/status?projectId={project_id}"
            print(f"\n🌐 API Call: GET {url}")
            print(f"🔍 Full URL: {url}")
            print(f"📊 Details: Get index status projectId={project_id}")
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            result = response.json()
            print(f"✅ Success: {result}")
            return result
        except Exception as e:
            print(f"❌ Call Failed: {str(e)}")
            return {"error": str(e)}
    
    def map_hunks_to_symbols(self, changes: List[Dict[str, Any]], project_id: str) -> Dict[str, Any]:
        """
        Map file changes to affected methods and classes.
        
        Args:
            changes: Changes list (FileChange format)
            project_id: Project ID
            
        Returns:
            Mapping result containing affected methods and classes
        """
        try:
            url = f"{self.base_url}/map/hunks-to-symbols?projectId={project_id}"
            payload = {"changes": changes}
            
            print(f"\n📋 Filtered changed files ({len(changes)} items):")
            print(f"🏷️  Project ID: {project_id}")
            for i, change in enumerate(changes, 1):
                path = change.get('path') or change.get('b_path') or change.get('a_path') or 'unknown'
                change_type = change.get('changeType') or change.get('change_type') or 'UNKNOWN'
                additions = change.get('additions')
                deletions = change.get('deletions')
                
                if additions is not None and deletions is not None:
                    stats = f"(+{additions:3d}/-{deletions:3d})"
                elif additions is not None:
                    stats = f"(+{additions} lines)"
                elif deletions is not None:
                    stats = f"(-{deletions} lines)"
                else:
                    stats = ""
                
                print(f"   {i:2d}. {path:<60} [{change_type:6}] {stats}")
            
            print(f"\n🌐 API Call: POST {url}")
            print(f"📦 Request Body: {len(changes)} file changes")
            print(f"🔍 Full URL: {url}")
            print(f"📊 Details: projectId={project_id}, changes={len(changes)} items")
            
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            print(f"✅ Success: {result}")
            return result
        except Exception as e:
            print(f"❌ Call Failed: {str(e)}")
            return {"error": str(e)}
    
    def analyze_impact(
        self,
        seeds: Dict[str, Any],
        project_id: str,
        depth: int = 1,
        direction: str = "outbound",
        include_edges: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze impact scope.
        
        Args:
            seeds: Seed methods/classes
            project_id: Project ID
            depth: Propagation depth
            direction: Direction (inbound/outbound/both)
            include_edges: Whether to include invocation edges
            
        Returns:
            Impact analysis result
        """
        try:
            url = f"{self.base_url}/analyze/impact?projectId={project_id}"
            payload = {
                "seeds": seeds,
                "direction": direction,
                "depth": depth,
                "includeEdges": include_edges
            }
            print(f"\n🌐 API Call: POST {url}")
            print(f"🏷️  Project ID: {project_id}")
            print(f"📦 Request Body: seeds={seeds}, depth={depth}, direction={direction}")
            print(f"🔍 Full URL: {url}")
            print(f"📊 Details: projectId={project_id}, seeds={len(seeds) if isinstance(seeds, list) else 1} items, depth={depth}, direction={direction}")
            
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            print(f"✅ Success: {result}")
            return result
        except Exception as e:
            print(f"❌ Call Failed: {str(e)}")
            return {"error": str(e)}


class SourceCodeTools:
    """Source code reading tools"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
    
    def read_file(self, relative_path: str, max_lines: int = 500, offset: int = 0) -> str:
        """
        Read file content in repository. Supports paginated reading for large files.
        
        Args:
            relative_path: Relative path to project root
            max_lines: Max lines to read
            offset: Starting line index (0-based)
            
        Returns:
            File content with metadata
        """
        try:
            file_path = self.repo_path / relative_path
            if not file_path.exists():
                return f"Error: File not found: {relative_path}"
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            paginated_content, meta_info = _paginate_lines(lines, offset, max_lines, relative_path, "File")
            
            return paginated_content + meta_info
            
        except Exception as e:
            return f"Error: {e}"
    
    def search_in_file(self, relative_path: str, keyword: str) -> List[Dict[str, Any]]:
        """
        Search keyword in a file.
        
        Args:
            relative_path: File path
            keyword: Search keyword
            
        Returns:
            List of matching lines
        """
        try:
            file_path = self.repo_path / relative_path
            if not file_path.exists():
                return [{"error": f"File not found: {relative_path}"}]
            
            matches = []
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if keyword in line:
                        matches.append({
                            "line_number": line_num,
                            "content": line.strip()
                        })
            
            return matches
        except Exception as e:
            return [{"error": str(e)}]
    
    def list_java_files(self, directory: str = "") -> List[str]:
        """
        List all Java files under a directory.
        
        Args:
            directory: Relative directory path
            
        Returns:
            List of Java file paths
        """
        try:
            search_path = self.repo_path / directory if directory else self.repo_path
            java_files = []
            
            for path in search_path.rglob("*.java"):
                relative_path = path.relative_to(self.repo_path)
                java_files.append(str(relative_path))
            
            return sorted(java_files)
        except Exception as e:
            return [f"Error: {e}"]
    
    def list_directory(self, directory: str = "") -> Dict[str, Any]:
        """
        List files and subdirectories in a given directory.
        
        Args:
            directory: Relative directory path, empty string indicates project root
            
        Returns:
            Dictionary containing directory content
        """
        try:
            target_path = self.repo_path / directory if directory else self.repo_path
            
            if not target_path.exists():
                return {"error": f"Directory does not exist: {directory or '.'}"}
            
            if not target_path.is_dir():
                return {"error": f"Not a directory: {directory or '.'}"}
            
            items = []
            for item in sorted(target_path.iterdir()):
                try:
                    relative = item.relative_to(self.repo_path)
                    if item.is_dir():
                        items.append({
                            "type": "directory",
                            "name": item.name,
                            "path": str(relative)
                        })
                    else:
                        size = item.stat().st_size
                        items.append({
                            "type": "file",
                            "name": item.name,
                            "path": str(relative),
                            "size": size
                        })
                except Exception:
                    continue
            
            return {
                "directory": directory or ".",
                "total_items": len(items),
                "directories": [i for i in items if i["type"] == "directory"],
                "files": [i for i in items if i["type"] == "file"]
            }
        except Exception as e:
            return {"error": str(e)}
    
    def find_file(self, pattern: str, max_results: int = 200) -> Dict[str, Any]:
        """
        Find files matching pattern in repository.
        
        Args:
            pattern: File pattern with wildcards
            max_results: Max results to return
            
        Returns:
            Dictionary containing matching files
        """
        import fnmatch
        
        try:
            matches = []
            
            for file_path in self.repo_path.rglob("*"):
                if file_path.is_file():
                    relative = file_path.relative_to(self.repo_path)
                    if fnmatch.fnmatch(file_path.name, pattern) or fnmatch.fnmatch(str(relative), pattern):
                        matches.append({
                            "name": file_path.name,
                            "path": str(relative),
                            "size": file_path.stat().st_size
                        })
                        if len(matches) >= max_results:
                            break
            
            result = {
                "pattern": pattern,
                "found_count": len(matches),
                "files": matches
            }
            
            if len(matches) >= max_results:
                result["note"] = f"Search limit reached, displaying first {max_results} results only"
            elif len(matches) == 0:
                result["note"] = f"No files matching '{pattern}' found"
            
            return result
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}


def get_all_tools(repo_path: str, java_analyzer_service_url: str) -> Dict[str, Any]:
    """
    Get all tool instances.
    
    Args:
        repo_path: Project path
        java_analyzer_service_url: Java source code analysis service URL
        
    Returns:
        Tools dictionary
    """
    return {
        "git": GitTools(repo_path),
        "api": AnalyzerAPITools(java_analyzer_service_url),
        "source": SourceCodeTools(repo_path)
    }
