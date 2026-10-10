import json
from typing import Dict, Any, List, Optional, Union
from apps.utils.logger_manager import get_logger

logger = get_logger(__name__)


class PostmanParser:
    """Parses Postman Collection v2.0 and v2.1 schemas into normalized API entities."""

    def __init__(self, collection_data: Union[str, Dict[str, Any]]):
        if isinstance(collection_data, str):
            try:
                self.collection = json.loads(collection_data.strip())
            except Exception as e:
                logger.error(f"Failed to parse Postman collection JSON: {e}")
                raise ValueError(f"Invalid JSON string for Postman collection: {e}")
        elif isinstance(collection_data, dict):
            self.collection = collection_data
        else:
            raise ValueError(f"Unsupported collection data type: {type(collection_data)}")

    def parse_endpoints(self) -> List[Dict[str, Any]]:
        """Recursively traverse item hierarchy and extract normalized API endpoints."""
        endpoints: List[Dict[str, Any]] = []
        raw_items = self.collection.get('item', [])
        self._extract_items_recursive(raw_items, endpoints, parent_tags=[])
        return endpoints

    def _extract_items_recursive(self, items: List[Dict[str, Any]], endpoints: List[Dict[str, Any]], parent_tags: List[str]):
        for it in items:
            if not isinstance(it, dict):
                continue

            # If it has sub-items, it's a folder/group
            if 'item' in it and isinstance(it['item'], list):
                folder_name = it.get('name', 'folder')
                self._extract_items_recursive(it['item'], endpoints, parent_tags + [folder_name])
                continue

            # Otherwise, it's a request item
            req = it.get('request')
            if not req:
                continue

            if isinstance(req, str):
                # String shorthand request URL (GET)
                method = "GET"
                raw_url = req
                query_params = []
                headers = []
                body_data = {}
                path_params = []
                from urllib.parse import urlparse
                parsed_path = urlparse(raw_url).path or '/'
            else:
                method = req.get('method', 'GET').upper()
                url_obj = req.get('url', {})

                if isinstance(url_obj, str):
                    raw_url = url_obj
                    query_params = []
                elif isinstance(url_obj, dict):
                    raw_url = url_obj.get('raw', '')
                    if not raw_url and 'path' in url_obj:
                        p = url_obj.get('path', [])
                        raw_url = "/" + "/".join(p) if isinstance(p, list) else str(p)
                    query_params = []
                    for q in url_obj.get('query', []):
                        if isinstance(q, dict) and q.get('key'):
                            query_params.append({
                                "name": q.get('key'),
                                "required": False,
                                "type": "string",
                                "example": str(q.get('value', ''))
                            })
                else:
                    raw_url = '/'
                    query_params = []

                headers = []
                for h in req.get('header', []):
                    if isinstance(h, dict) and h.get('key'):
                        headers.append({
                            "name": h.get('key'),
                            "required": False,
                            "type": "string",
                            "example": str(h.get('value', ''))
                        })

                # Request body extraction
                body_obj = req.get('body', {}) or {}
                body_data = {}
                mode = body_obj.get('mode')
                if mode == 'raw':
                    raw_text = body_obj.get('raw', '')
                    if raw_text:
                        try:
                            body_data = json.loads(raw_text)
                        except Exception:
                            body_data = {"raw": raw_text}
                elif mode == 'urlencoded':
                    body_data = {
                        param.get('key'): param.get('value', '')
                        for param in body_obj.get('urlencoded', [])
                        if isinstance(param, dict) and param.get('key')
                    }
                elif mode == 'formdata':
                    body_data = {
                        param.get('key'): param.get('value', '')
                        for param in body_obj.get('formdata', [])
                        if isinstance(param, dict) and param.get('key')
                    }

                # Path parameters from url variables
                path_params = []
                if isinstance(url_obj, dict):
                    for v in url_obj.get('variable', []):
                        if isinstance(v, dict) and v.get('key'):
                            path_params.append({
                                "name": v.get('key'),
                                "example": str(v.get('value', '')),
                                "type": "string"
                            })

                # Normalize path
                if isinstance(url_obj, dict) and isinstance(url_obj.get('path'), list):
                    path_segments = [
                        f"{{{str(p)[1:]}}}" if str(p).startswith(':') else str(p)
                        for p in url_obj['path']
                    ]
                    parsed_path = '/' + '/'.join(path_segments)
                elif raw_url.startswith(('http://', 'https://')):
                    from urllib.parse import urlparse
                    p_parsed = urlparse(raw_url)
                    parsed_path = p_parsed.path or '/'
                else:
                    import re
                    clean_path = re.sub(r'^\{\{[^}]+\}\}', '', raw_url).split('?', 1)[0]
                    parsed_path = clean_path if clean_path.startswith('/') else ('/' + clean_path if clean_path else '/')

            endpoints.append({
                "id": it.get('id') or f"{method}_{it.get('name', 'case').replace(' ', '_')}",
                "name": it.get('name') or parsed_path,
                "path": parsed_path,
                "method": method,
                "summary": it.get('name', ''),
                "tags": parent_tags or ['postman'],
                "query_params": query_params,
                "path_params": path_params,
                "headers": headers,
                "request_body_schema": {},
                "request_body_example": body_data,
                "responses": {"200": {"description": "OK"}}
            })
