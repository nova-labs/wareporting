import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv
from flask import Flask


@pytest.fixture
def wa_context():
    """Provide a Flask app/request context with a valid WA API token in session.

    - Loads `.env`
    - Verifies required env vars
    - Ensures project root is importable
    - Creates Flask app + pushes app and request contexts
    - Refreshes API token into Flask session
    """
    # Load env
    load_dotenv()

    # Verify required env vars
    required_env = [
        "WA_REPORTING_API_KEY",
        "WA_REPORTING_CLIENT_SECRET",
        "WA_REPORTING_FLASK_SECRET_KEY",
        "WA_REPORTING_DOMAIN",
    ]
    missing = [k for k in required_env if not os.getenv(k)]
    if missing:
        pytest.fail(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Set them in .env to run these tests.",
        )

    # Ensure project root import path
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # Minimal Flask app + contexts
    app = Flask(__name__)
    app.secret_key = os.environ["WA_REPORTING_FLASK_SECRET_KEY"]
    app_ctx = app.app_context()
    app_ctx.push()
    req_ctx = app.test_request_context()
    req_ctx.push()

    # Populate API token into session
    from auth import refresh_token  # noqa: WPS433 (import after path setup is intentional)

    err = refresh_token()
    if isinstance(err, str):
        # Clean up contexts before failing
        req_ctx.pop()
        app_ctx.pop()
        pytest.fail(f"Failed to get API token: {err}")

    # Yield control to the test
    yield app

    # Teardown
    req_ctx.pop()
    app_ctx.pop()

