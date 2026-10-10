import json
import yaml
from typing import Dict, Any, List, Optional, Union
from apps.utils.logger_manager import get_logger

logger = get_logger(__name__)


class OpenAPIParser:
    """Parses OpenAPI 3.x and Swagger 2.0 specifications into normalized API testing entities."""

    def __init__(self, spec_data: Union[str, Dict[str, Any]]):
        if isinstance(spec_data, str):
            self.raw_spec = self._parse_string_spec(spec_data)
        elif isinstance(spec_data, dict):
            self.raw_spec = spec_data
        else:
            raise ValueError(f"Unsupported spec data type: {type(spec_data)}")

        self.components = self.raw_spec.get('components', {}) or {}
        self.definitions = self.raw_spec.get('definitions', {}) or {}

    def _parse_string_spec(self, text: str) -> Dict[str, Any]:
        """Parse raw spec text as either JSON or YAML."""
        text = text.strip()
        try:
            return json.loads(text)
        except Exception:
            try:
                parsed = yaml.safe_load(text)
                if isinstance(parsed, dict):
                    return parsed
            except Exception as e:
                logger.error(f"Failed to parse OpenAPI spec as YAML: {e}")
        raise ValueError("Provided OpenAPI spec is neither valid JSON nor valid YAML.")

    def resolve_ref(self, ref: str, visited: Optional[set] = None) -> Dict[str, Any]:
        """Safely resolve $ref pointers with cycle detection."""
        if not ref or not isinstance(ref, str) or not ref.startswith('#/'):
            return {}

        if visited is None:
            visited = set()

        if ref in visited:
            logger.warning(f"Circular reference detected for {ref}; terminating recursion.")
            return {"type": "object", "description": f"circular_ref: {ref}"}

        visited.add(ref)
        parts = ref.lstrip('#/').split('/')
        curr = self.raw_spec
        for p in parts:
            if isinstance(curr, dict) and p in curr:
                curr = curr[p]
            else:
                return {}

        if isinstance(curr, dict) and '$ref' in curr:
            return self.resolve_ref(curr['$ref'], visited)

        return curr if isinstance(curr, dict) else {}

    def parse_endpoints(self) -> List[Dict[str, Any]]:
        """Extract and normalize all paths and operations into standard testing entities."""
        endpoints = []
        paths = self.raw_spec.get('paths', {}) or {}
        base_path = self.raw_spec.get('basePath', '')

        for path_pattern, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue

            full_path = f"{base_path.rstrip('/')}/{path_pattern.lstrip('/')}" if base_path else path_pattern
            common_params = path_item.get('parameters', []) or []

            for method in ('get', 'post', 'put', 'delete', 'patch', 'options', 'head'):
                if method not in path_item:
                    continue
                op = path_item[method]
                if not isinstance(op, dict):
                    continue

                operation_id = op.get('operationId', f"{method}_{path_pattern.replace('/', '_')}")
                summary = op.get('summary') or op.get('description') or operation_id
                tags = op.get('tags', ['default'])

                # Extract and normalize parameters
                all_params = list(common_params) + (op.get('parameters', []) or [])
                parsed_query = []
                parsed_path = []
                parsed_headers = []

                for param in all_params:
                    if '$ref' in param:
                        param = self.resolve_ref(param['$ref'])
                    in_location = param.get('in', 'query')
                    p_name = param.get('name', '')
                    p_required = param.get('required', False)
                    schema = param.get('schema', {})
                    if '$ref' in schema:
                        schema = self.resolve_ref(schema['$ref'])
                    p_type = schema.get('type') or param.get('type', 'string')
                    example = param.get('example') if param.get('example') is not None else schema.get('example', '')

                    param_dict = {
                        "name": p_name,
                        "required": p_required,
                        "type": p_type,
                        "example": str(example) if example is not None else ""
                    }

                    if in_location == 'query':
                        parsed_query.append(param_dict)
                    elif in_location == 'path':
                        parsed_path.append(param_dict)
                    elif in_location == 'header':
                        parsed_headers.append(param_dict)

                # Request body extraction (OpenAPI 3.x vs Swagger 2.0)
                body_schema = {}
                body_example = {}

                # OpenAPI 3.x
                if 'requestBody' in op:
                    rb = op['requestBody']
                    if '$ref' in rb:
                        rb = self.resolve_ref(rb['$ref'])
                    content = (rb.get('content') or {}).get('application/json', {})
                    b_schema = content.get('schema', {})
                    if '$ref' in b_schema:
                        b_schema = self.resolve_ref(b_schema['$ref'])
                    body_schema = b_schema
                    body_example = content.get('example') or self._synthesize_example_from_schema(body_schema)

                # Swagger 2.0 body param
                for param in all_params:
                    if param.get('in') == 'body':
                        b_schema = param.get('schema', {})
                        if '$ref' in b_schema:
                            b_schema = self.resolve_ref(b_schema['$ref'])
                        body_schema = b_schema
                        body_example = param.get('example') or self._synthesize_example_from_schema(body_schema)
                        break

                # Responses
                responses_data = {}
                for status_code, resp_obj in (op.get('responses', {}) or {}).items():
                    if '$ref' in resp_obj:
                        resp_obj = self.resolve_ref(resp_obj['$ref'])
                    responses_data[str(status_code)] = {
                        "description": resp_obj.get('description', '')
                    }

                endpoints.append({
                    "id": operation_id,
                    "name": summary,
                    "path": full_path,
                    "method": method.upper(),
                    "summary": summary,
                    "tags": tags,
                    "query_params": parsed_query,
                    "path_params": parsed_path,
                    "headers": parsed_headers,
                    "request_body_schema": body_schema,
                    "request_body_example": body_example,
                    "responses": responses_data
                })

        return endpoints

    def _synthesize_example_from_schema(self, schema: Dict[str, Any], depth: int = 0) -> Any:
        """Create a mock JSON example dictionary from schema properties."""
        if depth > 4 or not isinstance(schema, dict):
            return {}

        s_type = schema.get('type')
        if s_type == 'object' or 'properties' in schema:
            res = {}
            for prop_name, prop_spec in (schema.get('properties', {}) or {}).items():
                if '$ref' in prop_spec:
                    prop_spec = self.resolve_ref(prop_spec['$ref'])
                res[prop_name] = self._synthesize_example_from_schema(prop_spec, depth + 1)
            return res
        elif s_type == 'array':
            items_schema = schema.get('items', {})
            if '$ref' in items_schema:
                items_schema = self.resolve_ref(items_schema['$ref'])
            return [self._synthesize_example_from_schema(items_schema, depth + 1)]
        elif s_type == 'integer':
            return schema.get('example', 1)
        elif s_type == 'number':
            return schema.get('example', 1.0)
        elif s_type == 'boolean':
            return schema.get('example', True)
        else:
            return schema.get('example', 'sample_string')
