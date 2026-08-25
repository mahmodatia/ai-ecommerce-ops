from fastapi import Request


def request_actor(request: Request) -> str:
    """Return the authenticated operator name when auth is enabled."""
    return getattr(request.state, "user", "operator")
