"""
LangChain-based test scope analysis Agent.
Uses LangChain Agent framework for tool orchestration and decisions.
"""

from typing import Optional, List, Dict, Any
from .java_code_analyzer_tools import create_langchain_tools
from .prompts import JavaCodeAnalyzerPromptManager
from apps.llm.base import LLMServiceFactory
from django.conf import settings
import os
import json
import time
import logging

from .tools_callback_log import invoke_tool, log_node_start, log_node_end

from langgraph.graph import StateGraph, END


logger = logging.getLogger(__name__)


class JavaCodeAnalyzerAgent:
    """LangChain-based Java Code Analysis Agent"""
    
    def __init__(
        self,
        repo_path: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        java_analyzer_service_url: str = getattr(settings, 'JAVA_ANALYZER_SERVICE_URL'),
        max_iterations: int = None,  
        verbose: bool = True,
        llm_provider: Optional[str] = None,
    ):
        """
        Initialize Agent.
        
        Args:
            repo_path: Project repository path
            api_key: LLM API key
            base_url: API base URL
            java_analyzer_service_url: Java source code analysis service URL
            max_iterations: Max iteration count
            verbose: Whether to output verbose logs
            llm_provider: LLM provider name (deepseek/qwen)
        """
        self.repo_path = repo_path
        self.verbose = verbose
        
        # Deduce project_id from repo_path
        self.project_id = self._extract_project_id(repo_path)
        print("Inferred project_id from _extract_project_id is:", self.project_id)
        
        # Initialize prompt manager
        self.prompt_manager = JavaCodeAnalyzerPromptManager()
        
        llm_config = getattr(settings, 'LLM_PROVIDERS', {})
        provider = llm_provider or llm_config.get('default_provider', 'deepseek')
        provider_config = llm_config.get(provider, {})
        
        model = provider_config.get('model')
        self.model = model
        
        provider_name = model.split('-')[0].lower()
        if 'qwen' in provider_name:
            provider_name = 'qwen'
        if 'deepseek' in provider_name:
            provider_name = 'deepseek'
        
        self.llm = LLMServiceFactory.create(provider_name)
        self.tools = create_langchain_tools(repo_path, java_analyzer_service_url, self.project_id)
        self.max_iterations = max_iterations

    def _get_tool_by_name(self, name: str):
        """Get tool instance by name from registered LangChain tools.

        Args:
            name: Tool name (matching BaseTool.name)

        Returns:
            Matching tool object.

        Raises:
            ValueError: Tool not found.
        """
        for tool in self.tools:
            if getattr(tool, "name", None) == name:
                return tool
        raise ValueError(f"Tool not found: {name}")

    def _safe_json_loads(self, s: Any) -> Any:
        """Parse string to JSON if possible; otherwise return as-is."""
        if isinstance(s, (dict, list)):
            return s
        if not isinstance(s, str):
            return s
        try:
            return json.loads(s)
        except Exception:
            return s

    def _merge_seeds(self, seeds_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge multiple map_hunks_to_symbols seed outputs and deduplicate."""
        merged: Dict[str, Any] = {"methods": [], "classes": []}
        seen_methods = set()
        seen_classes = set()

        for seeds in seeds_list:
            if not isinstance(seeds, dict):
                continue

            methods = seeds.get("methods") or []
            classes = seeds.get("classes") or []

            if isinstance(methods, list):
                for m in methods:
                    if not isinstance(m, dict):
                        continue
                    key = (
                        m.get("fqnClass"),
                        m.get("methodName"),
                        tuple(m.get("paramTypes") or []),
                    )
                    if key in seen_methods:
                        continue
                    seen_methods.add(key)
                    merged["methods"].append(m)

            if isinstance(classes, list):
                for c in classes:
                    if not isinstance(c, str):
                        continue
                    if c in seen_classes:
                        continue
                    seen_classes.add(c)
                    merged["classes"].append(c)

        return merged

    def _build_langgraph(self):
        """Build LangGraph workflow (deterministic tool invocation + final LLM report generation)."""

        index_project = self._get_tool_by_name("index_project")
        get_index_status = self._get_tool_by_name("get_index_status")
        get_commit_info = self._get_tool_by_name("get_commit_info")
        get_changed_files_detailed = self._get_tool_by_name("get_changed_files_detailed")
        get_file_diff = self._get_tool_by_name("get_file_diff")
        map_hunks_to_symbols = self._get_tool_by_name("map_hunks_to_symbols")
        analyze_impact = self._get_tool_by_name("analyze_impact")

        def _invoke_tool(tool, args: Dict[str, Any], *, label: str) -> Any:
            return invoke_tool(logger, tool, args, label=label)

        def _log_node_start(name: str, state: Dict[str, Any]) -> float:
            return log_node_start(logger, name, state, project_id=self.project_id)

        def _log_node_end(name: str, start: float, **extra) -> None:
            return log_node_end(logger, name, start, **extra)

        def node_index(state: Dict[str, Any]) -> Dict[str, Any]:
            """Node: trigger project indexing (index_project)."""
            t0 = _log_node_start("index", state)
            if self.verbose:
                print("\n🧩 [LangGraph] index_project")
            out = _invoke_tool(index_project, {"project_id": self.project_id}, label="index_project")
            _log_node_end("index", t0)
            return {**state, "index_result": out}

        def node_wait_ready(state: Dict[str, Any]) -> Dict[str, Any]:
            """Node: poll index status until READY or timeout."""
            t0 = _log_node_start("wait_ready", state)
            if self.verbose:
                print("\n🧩 [LangGraph] wait_index_ready")

            max_attempts = 30
            last = None
            for i in range(max_attempts):
                out = _invoke_tool(
                    get_index_status,
                    {"project_id": self.project_id},
                    label=f"get_index_status[{i+1}]",
                )
                last = out
                parsed = self._safe_json_loads(out)
                status = None
                if isinstance(parsed, dict):
                    status = parsed.get("status") or parsed.get("state")
                if self.verbose:
                    print(f"   attempt={i+1}/{max_attempts}, status={status}")
                if status == "READY":
                    break
                time.sleep(1)
            _log_node_end("wait_ready", t0, last_status=status)
            return {**state, "index_status": last}

        def node_commits(state: Dict[str, Any]) -> Dict[str, Any]:
            """Node: get commit info for both base and new commits (get_commit_info)."""
            t0 = _log_node_start("commits", state)
            if self.verbose:
                print("\n🧩 [LangGraph] get_commit_info")
            base_commit = state.get("base_commit")
            new_commit = state.get("new_commit")
            if not base_commit or not new_commit:
                raise KeyError("base_commit/new_commit missing in state")
            base_info = _invoke_tool(get_commit_info, {"commit_hash": base_commit}, label="get_commit_info.base")
            new_info = _invoke_tool(get_commit_info, {"commit_hash": new_commit}, label="get_commit_info.new")
            _log_node_end("commits", t0)
            return {**state, "base_commit_info": base_info, "new_commit_info": new_info}

        def node_changes(state: Dict[str, Any]) -> Dict[str, Any]:
            """Node: get changed files and hunks details (get_changed_files_detailed)."""
            t0 = _log_node_start("changes", state)
            if self.verbose:
                print("\n🧩 [LangGraph] get_changed_files_detailed")
            base_commit = state.get("base_commit")
            new_commit = state.get("new_commit")
            if not base_commit or not new_commit:
                raise KeyError("base_commit/new_commit missing in state")
            out = _invoke_tool(
                get_changed_files_detailed,
                {"base_commit": base_commit, "new_commit": new_commit},
                label="get_changed_files_detailed",
            )
            parsed = self._safe_json_loads(out)
            changes_count = len(parsed) if isinstance(parsed, list) else None
            _log_node_end("changes", t0, changes_count=changes_count)
            return {**state, "changed_files_detailed": out}

        def node_diff_snippets(state: Dict[str, Any]) -> Dict[str, Any]:
            """Node: fetch diff for Top changed files and extract Before/After snippets."""
            t0 = _log_node_start("diff_snippets", state)
            if self.verbose:
                print("\n🧩 [LangGraph] get_file_diff (snippets)")

            base_commit = state.get("base_commit")
            new_commit = state.get("new_commit")
            raw = state.get("changed_files_detailed")
            parsed = self._safe_json_loads(raw)
            if not isinstance(parsed, list):
                _log_node_end("diff_snippets", t0, selected=0)
                return {**state, "diff_snippets": {}}

            def _score(c: Dict[str, Any]) -> int:
                add = c.get("additions")
                dele = c.get("deletions")
                if isinstance(add, int) and isinstance(dele, int):
                    return add + dele
                hunks = c.get("hunks")
                if isinstance(hunks, list):
                    return len(hunks)
                return 0

            candidates = [c for c in parsed if isinstance(c, dict) and c.get("path")]
            candidates = sorted(candidates, key=_score, reverse=True)
            selected = candidates[:5]

            def _extract_before_after(diff_text: Any, *, max_lines: int = 80) -> Dict[str, str]:
                """Extract 'before' and 'after' code snippets from unified diff text."""
                text = diff_text if isinstance(diff_text, str) else str(diff_text)
                before_lines: List[str] = []
                after_lines: List[str] = []
                for line in text.splitlines():
                    if (
                        line.startswith("diff --git ")
                        or line.startswith("index ")
                        or line.startswith("--- ")
                        or line.startswith("+++ ")
                        or line.startswith("@@")
                    ):
                        continue
                    if line.startswith("-") and not line.startswith("---"):
                        before_lines.append(line[1:])
                        continue
                    if line.startswith("+") and not line.startswith("+++"):
                        after_lines.append(line[1:])
                        continue
                    if line.startswith(" "):
                        before_lines.append(line[1:])
                        after_lines.append(line[1:])
                        continue
                if len(before_lines) > max_lines:
                    before_lines = before_lines[:max_lines]
                if len(after_lines) > max_lines:
                    after_lines = after_lines[:max_lines]
                return {
                    "before": "\n".join(before_lines).strip(),
                    "after": "\n".join(after_lines).strip(),
                }

            snippets: Dict[str, Any] = {}
            for item in selected:
                path = str(item.get("path"))
                try:
                    diff_text = _invoke_tool(
                        get_file_diff,
                        {
                            "base_commit": base_commit,
                            "new_commit": new_commit,
                            "file_path": path,
                            "offset": 0,
                            "limit": 200,
                        },
                        label=f"get_file_diff:{path}",
                    )
                    snippets[path] = _extract_before_after(diff_text)
                except Exception as e:
                    snippets[path] = {"before": "", "after": f"Error: {e}"}

            _log_node_end("diff_snippets", t0, selected=len(selected))
            return {**state, "diff_snippets": snippets}

        def node_map_symbols(state: Dict[str, Any]) -> Dict[str, Any]:
            """Node: map changed hunks to Java symbols (classes/methods) and aggregate seeds."""
            t0 = _log_node_start("map_symbols", state)
            if self.verbose:
                print("\n🧩 [LangGraph] map_hunks_to_symbols (batched)")

            raw = state.get("changed_files_detailed")
            parsed = self._safe_json_loads(raw)
            if not isinstance(parsed, list):
                return {**state, "map_results": [], "seeds": {"methods": [], "classes": []}}

            java_changes = [c for c in parsed if isinstance(c, dict) and str(c.get("path", "")).endswith(".java")]
            batch_size = 15
            map_outputs: List[Any] = []
            seeds_candidates: List[Dict[str, Any]] = []

            for i in range(0, len(java_changes), batch_size):
                batch = java_changes[i : i + batch_size]
                changes_json = json.dumps(batch, ensure_ascii=False)
                out = _invoke_tool(
                    map_hunks_to_symbols,
                    {"changes": changes_json, "project_id": self.project_id},
                    label=f"map_hunks_to_symbols[{i//batch_size+1}]",
                )
                map_outputs.append(out)
                out_parsed = self._safe_json_loads(out)

                if isinstance(out_parsed, dict):
                    if isinstance(out_parsed.get("methods"), list) or isinstance(out_parsed.get("classes"), list):
                        seeds_candidates.append({
                            "methods": out_parsed.get("methods") or [],
                            "classes": out_parsed.get("classes") or [],
                        })
                    else:
                        for k in ("data", "result", "seeds"):
                            inner = out_parsed.get(k)
                            if isinstance(inner, dict) and (isinstance(inner.get("methods"), list) or isinstance(inner.get("classes"), list)):
                                seeds_candidates.append({
                                    "methods": inner.get("methods") or [],
                                    "classes": inner.get("classes") or [],
                                })
                                break

            merged_seeds = self._merge_seeds(seeds_candidates)
            _log_node_end(
                "map_symbols",
                t0,
                java_files=len(java_changes),
                methods=len(merged_seeds.get("methods") or []),
                classes=len(merged_seeds.get("classes") or []),
            )
            return {**state, "map_results": map_outputs, "seeds": merged_seeds}

        def node_impact(state: Dict[str, Any]) -> Dict[str, Any]:
            """Node: invoke analyze_impact to calculate call graph impact scope."""
            t0 = _log_node_start("impact", state)
            if self.verbose:
                print("\n🧩 [LangGraph] analyze_impact")

            seeds = state.get("seeds") or {"methods": [], "classes": []}
            seeds_json = json.dumps(seeds, ensure_ascii=False)
            out = _invoke_tool(
                analyze_impact,
                {
                    "seeds": seeds_json,
                    "project_id": self.project_id,
                    "depth": 3,
                    "direction": "both",
                    "include_edges": True,
                },
                label="analyze_impact",
            )
            _log_node_end("impact", t0)
            return {**state, "impact_result": out}

        def node_render(state: Dict[str, Any]) -> Dict[str, Any]:
            """Node: synthesize factual data and invoke LLM to generate final Markdown report."""
            t0 = _log_node_start("render", state)
            if self.verbose:
                print("\n🧩 [LangGraph] render_markdown")

            base_info = state.get("base_commit_info", "")
            new_info = state.get("new_commit_info", "")
            changes = state.get("changed_files_detailed", "")
            map_results = state.get("map_results", [])
            impact = state.get("impact_result", "")
            diff_snippets = state.get("diff_snippets") or {}

            def clip(x: Any, limit: int = 20000) -> str:
                if x is None:
                    return ""
                if not isinstance(x, str):
                    try:
                        x = json.dumps(x, ensure_ascii=False)
                    except Exception:
                        x = str(x)
                return x if len(x) <= limit else x[:limit] + "\n...<truncated>"

            def safe_parse_json(value: Any) -> Any:
                try:
                    return self._safe_json_loads(value)
                except Exception:
                    return value

            def summarize_changes(changes_value: Any) -> Dict[str, Any]:
                parsed = safe_parse_json(changes_value)
                if not isinstance(parsed, list):
                    return {
                        "total": None,
                        "java_count": None,
                        "top_files": [],
                        "raw_type": type(parsed).__name__,
                    }

                total = len(parsed)
                java_items = [c for c in parsed if isinstance(c, dict) and str(c.get("path", "")).endswith(".java")]

                def _line_count(c: Dict[str, Any]) -> int:
                    for k in ("lines_changed", "changed_lines", "changed", "additions", "deletions"):
                        v = c.get(k)
                        if isinstance(v, int):
                            return v
                    hunks = c.get("hunks")
                    if isinstance(hunks, list):
                        return len(hunks)
                    return 0

                sorted_items = sorted(
                    [c for c in parsed if isinstance(c, dict)],
                    key=_line_count,
                    reverse=True,
                )
                top = []
                for c in sorted_items[:12]:
                    top.append({
                        "path": c.get("path"),
                        "status": c.get("status") or c.get("change_type") or c.get("type"),
                        "lines_changed": _line_count(c),
                    })

                return {
                    "total": total,
                    "java_count": len(java_items),
                    "top_files": top,
                }

            def summarize_impact(impact_value: Any) -> Dict[str, Any]:
                parsed = safe_parse_json(impact_value)
                if isinstance(parsed, dict):
                    nodes = parsed.get("nodes")
                    edges = parsed.get("edges")
                    return {
                        "nodes_count": len(nodes) if isinstance(nodes, list) else None,
                        "edges_count": len(edges) if isinstance(edges, list) else None,
                        "raw_keys": list(parsed.keys())[:20],
                    }
                return {"nodes_count": None, "edges_count": None, "raw_type": type(parsed).__name__}

            changes_summary = summarize_changes(changes)
            seeds_summary = state.get("seeds") or {"methods": [], "classes": []}
            impact_summary = summarize_impact(impact)

            template = self.prompt_manager.get_system_prompt()
            if not template:
                raise ValueError("java_code_analyzer_system_prompt is empty in prompt_config.yaml")

            prompt = template.format_map({
                "repo_path": self.repo_path,
                "project_id": self.project_id,
                "base_commit": state.get("base_commit"),
                "new_commit": state.get("new_commit"),
                "summary_changed_files": json.dumps(changes_summary, ensure_ascii=False),
                "summary_seeds": json.dumps(seeds_summary, ensure_ascii=False),
                "summary_impact": json.dumps(impact_summary, ensure_ascii=False),
                "raw_base_commit_info": clip(base_info),
                "raw_new_commit_info": clip(new_info),
                "raw_changed_files_detailed": clip(changes, limit=12000),
                "raw_map_hunks_to_symbols_outputs": clip(map_results, limit=12000),
                "raw_analyze_impact_result": clip(impact, limit=12000),
                "raw_diff_snippets": clip(diff_snippets, limit=12000),
            })

            llm_out = self.llm.invoke(prompt)
            content = getattr(llm_out, "content", llm_out)
            _log_node_end("render", t0, markdown_len=len(content) if isinstance(content, str) else None)
            return {**state, "final_markdown": content}

        builder = StateGraph(dict)
        builder.add_node("index", node_index)
        builder.add_node("wait_ready", node_wait_ready)
        builder.add_node("commits", node_commits)
        builder.add_node("changes", node_changes)
        builder.add_node("diff_snippets", node_diff_snippets)
        builder.add_node("map_symbols", node_map_symbols)
        builder.add_node("impact", node_impact)
        builder.add_node("render", node_render)

        builder.set_entry_point("index")
        builder.add_edge("index", "wait_ready")
        builder.add_edge("wait_ready", "commits")
        builder.add_edge("commits", "changes")
        builder.add_edge("changes", "diff_snippets")
        builder.add_edge("diff_snippets", "map_symbols")
        builder.add_edge("map_symbols", "impact")
        builder.add_edge("impact", "render")
        builder.add_edge("render", END)

        return builder.compile()
    
    def analyze(self, base_commit: str, new_commit: str) -> Dict[str, Any]:
        """
        Analyze change impact between two commits.
        
        Args:
            base_commit: Base commit hash
            new_commit: Target commit hash
            
        Returns:
            Dictionary containing analysis results
        """
        if self.verbose:
            print("="*70)
            print("🤖 Starting LangGraph workflow analysis")
            print("="*70)
            print(f"📁 Repository: {self.repo_path}")
            print(f"🔄 Changes: {base_commit[:8]} → {new_commit[:8]}")
            print(f"🏷️  project_id: {self.project_id}")
            print(f"🧠 Model: {getattr(self.llm, 'model_name', self.model)}")
            print("="*70)
            print()

        graph = self._build_langgraph()

        try:
            result_state = graph.invoke({
                "base_commit": base_commit,
                "new_commit": new_commit,
            })

            final_output = result_state.get("final_markdown", "")

            if self.verbose:
                print(f"\n{'='*70}")
                print("✅ LangGraph execution completed")
                print(f"{'='*70}")
                print(f"Final output length: {len(final_output)} characters")
                if final_output:
                    print(f"Final output preview: {final_output[:200]}{'...' if len(final_output) > 200 else ''}")
                print(f"{'='*70}\n")

            return {
                "output": final_output,
                "intermediate_steps": [],
                "success": True,
                "langgraph_state": {
                    "index_result": result_state.get("index_result"),
                    "index_status": result_state.get("index_status"),
                    "base_commit_info": result_state.get("base_commit_info"),
                    "new_commit_info": result_state.get("new_commit_info"),
                    "changed_files_detailed": result_state.get("changed_files_detailed"),
                    "map_results": result_state.get("map_results"),
                    "impact_result": result_state.get("impact_result"),
                },
            }
        except Exception as e:
            error_str = str(e)
            if self.verbose:
                print(f"\n❌ Agent execution failed: {error_str}")
            
            if "JSONDecodeError" in error_str or "Unterminated string" in error_str:
                friendly_error = f"""## Tool Call Parameter Format Error

**Cause**: LLM encountered a formatting error when generating tool call arguments.

**Possible reasons**:
- LLM generated invalid JSON format
- Special characters mixed into parameters
- String quotes unterminated

**Suggested solutions**:
1. Check if input commit hash contains special characters
2. Try re-running the analysis
3. If issue persists, adjust prompt or model parameters

**Original error**: {error_str}"""
            elif "invalid_tool_call" in error_str.lower() or "tool_calls" in error_str.lower():
                friendly_error = f"""## Tool Call Failed

**Cause**: LLM-generated tool call does not conform to requirements.

**Possible reasons**:
- Tool name or parameter format error
- Tool does not exist or parameter type mismatch

**Suggested solutions**:
1. Verify tool name
2. Check parameter format and types
3. Re-run analysis

**Original error**: {error_str}"""
            else:
                friendly_error = f"""## Analysis Execution Failed

**Cause**: {error_str}

**Suggested solutions**:
1. Check repository path and Git repository state
2. Ensure network connection is active
3. Verify input parameter format
4. Re-run analysis

If problem persists, contact technical support."""
            
            return {
                "output": friendly_error,
                "intermediate_steps": [],
                "success": False,
                "error": error_str,
                "error_type": "json_parse_error" if "JSONDecodeError" in error_str else "execution_error"
            }
    
    def _monitor_required_steps(self, tool_name: str, args: dict) -> None:
        """Monitor execution of required steps"""
        pass
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools"""
        return [tool.name for tool in self.tools]
    
    def _extract_project_id(self, repo_path: str) -> str:
        """
        Extract project_id from repo_path
        
        Args:
            repo_path: Repository path
            
        Returns:
            project_id: Project identifier
        """
        project_mapping = getattr(settings, 'PROJECT_ID_REPO_MAPPING', {})
        base_dir = getattr(settings, 'JAVA_PROJECTS_BASE_DIR', '/home')
        
        for project_id in project_mapping.keys():
            expected_path = os.path.join(base_dir, project_id)
            if repo_path == expected_path or repo_path.startswith(expected_path):
                return project_id
        
        basename = os.path.basename(repo_path.rstrip('/'))
        return basename