import io
import json
import zipfile
import uuid
from typing import List, Dict, Any, Optional


class XMindExporter:
    """XMind MindMap visual test suite exporter.
    
    Generates interactive .xmind workbook archives and hierarchical
    Markdown mindmap outlines organizing test cases by Priority and Steps.
    """

    def __init__(self, root_title: str = "CodeBrain QA Suite"):
        self.root_title = root_title

    def _generate_topic_node(self, title: str, children: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Generate a standard XMind topic node."""
        node = {
            "id": uuid.uuid4().hex,
            "title": title
        }
        if children:
            node["children"] = {
                "attached": children
            }
        return node

    def generate_mindmap_data(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Hierarchically group test cases into Root -> Priority -> Scenario -> Steps."""
        grouped_by_priority: Dict[str, List[Dict[str, Any]]] = {}

        for tc in test_cases:
            prio = tc.get('priority', 'P2') or 'P2'
            grouped_by_priority.setdefault(prio.upper(), []).append(tc)

        priority_nodes = []
        for prio_key in ["P0", "P1", "P2", "P3"]:
            cases = grouped_by_priority.get(prio_key, [])
            if not cases:
                continue

            case_nodes = []
            for tc in cases:
                title = tc.get('title') or tc.get('name') or tc.get('description', 'Test Case')
                steps_raw = tc.get('test_steps', [])
                expected_raw = tc.get('expected_results', [])

                steps_list = steps_raw if isinstance(steps_raw, list) else [s.strip() for s in str(steps_raw).split('\n') if s.strip()]
                expected_list = expected_raw if isinstance(expected_raw, list) else [e.strip() for e in str(expected_raw).split('\n') if e.strip()]

                step_nodes = [self._generate_topic_node(f"Step {idx}: {s}") for idx, s in enumerate(steps_list, start=1)]
                expected_nodes = [self._generate_topic_node(f"Expect {idx}: {e}") for idx, e in enumerate(expected_list, start=1)]

                detail_children = []
                if step_nodes:
                    detail_children.append(self._generate_topic_node("Actions / Steps", step_nodes))
                if expected_nodes:
                    detail_children.append(self._generate_topic_node("Expected Outcomes", expected_nodes))

                case_node = self._generate_topic_node(title, detail_children if detail_children else None)
                case_nodes.append(case_node)

            prio_node = self._generate_topic_node(f"Priority {prio_key} ({len(cases)} cases)", case_nodes)
            priority_nodes.append(prio_node)

        root_topic = self._generate_topic_node(self.root_title, priority_nodes)
        return {
            "id": uuid.uuid4().hex,
            "title": self.root_title,
            "rootTopic": root_topic
        }

    def generate_xmind_archive(self, test_cases: List[Dict[str, Any]]) -> bytes:
        """Create a valid .xmind ZIP archive containing content.json and metadata."""
        sheet_data = self.generate_mindmap_data(test_cases)
        content_json = json.dumps([sheet_data], ensure_ascii=False, indent=2)

        metadata_json = json.dumps({
            "creator": {"name": "CodeBrain QA Framework", "version": "2.0"}
        }, indent=2)

        manifest_json = json.dumps({
            "file-entries": {
                "content.json": {},
                "metadata.json": {}
            }
        }, indent=2)

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("content.json", content_json.encode('utf-8'))
            zip_file.writestr("metadata.json", metadata_json.encode('utf-8'))
            zip_file.writestr("manifest.json", manifest_json.encode('utf-8'))

        buffer.seek(0)
        return buffer.getvalue()

    def generate_markdown_mindmap(self, test_cases: List[Dict[str, Any]]) -> str:
        """Generate Markmap/Markdown compatible hierarchical tree outline."""
        lines = [f"# {self.root_title}\n"]

        grouped_by_priority: Dict[str, List[Dict[str, Any]]] = {}
        for tc in test_cases:
            prio = tc.get('priority', 'P2') or 'P2'
            grouped_by_priority.setdefault(prio.upper(), []).append(tc)

        for prio_key in ["P0", "P1", "P2", "P3"]:
            cases = grouped_by_priority.get(prio_key, [])
            if not cases:
                continue

            lines.append(f"## Priority {prio_key} ({len(cases)} cases)\n")
            for tc in cases:
                title = tc.get('title') or tc.get('name') or tc.get('description', 'Test Case')
                lines.append(f"### {title}")
                
                steps_raw = tc.get('test_steps', [])
                steps_list = steps_raw if isinstance(steps_raw, list) else [s.strip() for s in str(steps_raw).split('\n') if s.strip()]
                if steps_list:
                    lines.append("- **Steps**")
                    for s in steps_list:
                        lines.append(f"  - {s}")

                expected_raw = tc.get('expected_results', [])
                expected_list = expected_raw if isinstance(expected_raw, list) else [e.strip() for e in str(expected_raw).split('\n') if e.strip()]
                if expected_list:
                    lines.append("- **Expected Results**")
                    for e in expected_list:
                        lines.append(f"  - {e}")
                lines.append("")

        return "\n".join(lines)
