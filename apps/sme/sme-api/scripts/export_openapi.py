"""Dumps the current OpenAPI schema to a committed file (apps/sme/sme-api/openapi.json),
so a future integration (a second or third component) has a durable, offline contract
to code against instead of only a live /openapi.json on a running server.

Re-run and commit the result after any route change:
    cd apps/sme/sme-api && python scripts/export_openapi.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app  # noqa: E402


def main() -> None:
    schema = app.openapi()
    out = Path(__file__).parent.parent / "openapi.json"
    out.write_text(json.dumps(schema, indent=2) + "\n")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
