from backend.main import app


def _methods(path):
    return {m for r in app.routes if getattr(r, "path", None) == path for m in r.methods}


def test_download_model_is_post_only():
    # A GET would let any web page start a multi-GB download via <img>/<script>.
    assert _methods("/api/download_model") == {"POST"}


def test_cors_is_not_wildcard():
    cors = [m for m in app.user_middleware if m.cls.__name__ == "CORSMiddleware"][0]
    assert "*" not in cors.kwargs["allow_origins"]
