"""
mitmproxy addon to capture Mordor Intelligence API calls.

Run with: mitmproxy -s mitmproxy/scripts/mordor_capture.py
"""

import json
import os
from datetime import datetime
from mitmproxy import http, ctx

CAPTURE_DIR = "mitmproxy/flows"
TARGET_DOMAIN = "mordorintelligence.com"

class MordorCapture:
    def __init__(self):
        self.captured = []
        os.makedirs(CAPTURE_DIR, exist_ok=True)

    def response(self, flow: http.HTTPFlow) -> None:
        if TARGET_DOMAIN not in flow.request.pretty_host:
            return

        # Log API calls and page requests
        entry = {
            "timestamp": datetime.now().isoformat(),
            "url": flow.request.pretty_url,
            "method": flow.request.method,
            "status": flow.response.status_code,
            "content_type": flow.response.headers.get("content-type", ""),
            "size": len(flow.response.content),
        }

        # Capture JSON API responses
        if "application/json" in entry["content_type"]:
            try:
                entry["body"] = json.loads(flow.response.content)
            except:
                pass

        self.captured.append(entry)
        ctx.log.info(f"[MORDOR] {entry['method']} {entry['url'][:80]}...")

        # Save periodically
        if len(self.captured) % 10 == 0:
            self._save()

    def _save(self):
        outfile = f"{CAPTURE_DIR}/capture_{datetime.now():%Y%m%d_%H%M}.json"
        with open(outfile, "w") as f:
            json.dump(self.captured, f, indent=2, default=str)
        ctx.log.info(f"[MORDOR] Saved {len(self.captured)} entries to {outfile}")

addons = [MordorCapture()]
