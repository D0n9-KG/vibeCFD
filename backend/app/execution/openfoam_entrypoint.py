from __future__ import annotations

import json
import os
from pathlib import Path


def main() -> None:
    request_path = os.getenv("SUBMARINE_OPENFOAM_REQUEST", "").strip()
    if not request_path:
        raise SystemExit("SUBMARINE_OPENFOAM_REQUEST is required.")

    manifest = Path(request_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    print(json.dumps({"status": "adapter-ready", "request": payload}, ensure_ascii=False))


if __name__ == "__main__":
    main()
