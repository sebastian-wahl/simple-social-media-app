from __future__ import annotations

import json
from pathlib import Path

from social_media_app.app import app

# Since FastAPI provides an openapi spec itself at the endpoint /openapi.json
# we dont need to define a specification ourselves.
# But for the sake of completeness we generate the specification and place
# it in the backend folder for closer inspection.


def main() -> None:
    """
    Generate an OpenAPI JSON file from the FastAPI app and write it to
    the backend directory as openapi.json.
    """
    schema = app.openapi()

    output_path = Path(__file__).resolve().parents[2] / "openapi.json"

    output_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    print(f"OpenAPI schema written to: {output_path}")


if __name__ == "__main__":
    main()
