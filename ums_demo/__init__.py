from .populate import generate


def post_init_hook(env):
    """Populate every UMS screen with demo records (idempotent)."""
    generate(env)
