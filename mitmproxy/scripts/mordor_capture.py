"""
mitmproxy addon to capture Mordor Intelligence API calls.

Run with: mitmproxy -s mitmproxy/scripts/mordor_capture.py
"""

import json
import os
from pathlib import Path
from datetime import datetime
from mitmproxy import http, ctx

# Use absolute path based on script location
SCRIPT_DIR = Path(__file__).parent.parent
CAPTURE_DIR = SCRIPT_DIR / "flows"
TARGET_DOMAIN = "mordorintelligence.com"

class MordorCapture:
    def __init__(self):
        self.captured = []
        self.capture_file = None
        CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
        ctx.log.info(f"[MORDOR] Capture directory: {CAPTURE_DIR}")

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
            except Exception as e:
                ctx.log.warn(f"[MORDOR] Failed to parse JSON: {e}")

        self.captured.append(entry)
        ctx.log.info(f"[MORDOR] {entry['method']} {entry['url'][:80]}... ({len(self.captured)} total)")

        # Save after every response
        self._save()

    def _save(self):
        try:
            self.capture_file = CAPTURE_DIR / f"capture_{datetime.now():%Y%m%d_%H%M%S}.json"
            with open(self.capture_file, "w") as f:
                json.dump(self.captured, f, indent=2, default=str)
            ctx.log.info(f"[MORDOR] Exported {len(self.captured)} entries to {self.capture_file.name}")
        except Exception as e:
            ctx.log.error(f"[MORDOR] Failed to save: {e}")

    def done(self):
        """Called when mitmproxy exits"""
        if self.captured:
            self._save()
            ctx.log.info(f"[MORDOR] Final export: {len(self.captured)} entries saved")

addons = [MordorCapture()]
