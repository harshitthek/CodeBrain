"""
SSE (Server-Sent Events) streaming log transmission view.

Provides real-time log push functionality based on Server-Sent Events.
Uses queue mechanism to implement producer-consumer pattern, supporting concurrent tasks.
"""

import json
import time
from typing import Iterator
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from ..utils.sse_bus import get_queue


@csrf_exempt
def stream_logs(request):
    task_id = request.GET.get("task_id")
    if not task_id:
        return StreamingHttpResponse(b"missing task_id", status=400)

    q, _ = get_queue(task_id)

    def event_stream() -> Iterator[bytes]:
        yield b": stream-start\n\n"
        while True:
            try:
                item = q.get(timeout=15.0)
            except Exception:
                item = None
            if item is None:
                payload = json.dumps({
                    "ts": int(time.time())
                }, ensure_ascii=False).encode("utf-8")
                yield b"event: progress\n"
                yield b"data: " + payload + b"\n\n"
                continue

            if hasattr(item, 'dict'):
                item_dict = item.dict()
            else:
                item_dict = item
                
            data = json.dumps(item_dict, ensure_ascii=False).encode("utf-8")
            yield b"id: %d\n" % item_dict["seq"]
            yield b"event: log\n"
            yield b"data: " + data + b"\n\n"

    resp = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    resp["Cache-Control"] = "no-cache"
    resp["X-Accel-Buffering"] = "no"
    return resp
