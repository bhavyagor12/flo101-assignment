"""Build the FastAPI app, dump app.openapi() to <repo>/openapi.json.
The web `type-gen` task feeds that file into openapi-typescript.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from flo101_api.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[5]
OPENAPI_OUT = REPO_ROOT / "openapi.json"


def main() -> int:
    app = create_app()
    schema = app.openapi()
    OPENAPI_OUT.parent.mkdir(parents=True, exist_ok=True)
    OPENAPI_OUT.write_text(json.dumps(schema, indent=2, sort_keys=True))
    rel = OPENAPI_OUT.relative_to(REPO_ROOT)
    print(f"✓ wrote {rel} ({len(schema.get('paths', {}))} paths, "
          f"{len(schema.get('components', {}).get('schemas', {}))} schemas)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
