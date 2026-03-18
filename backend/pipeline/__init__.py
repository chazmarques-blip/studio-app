"""Pipeline package: modular AI campaign generation pipeline.

This package breaks down the monolithic pipeline.py into focused modules:
- config.py: Constants, models, and configuration data
- utils.py: Storage, text parsing, and AI utility functions
- prompts.py: AI agent prompt construction
- media.py: Image and video generation/processing
- engine.py: Step execution, recovery, and state management
- avatar_routes.py: Avatar-related API endpoints
- routes.py: Core pipeline API endpoints
- router.py: Shared FastAPI router instance
"""

from pipeline.router import router

# Import route modules to register their endpoints on the shared router
from pipeline import routes  # noqa: F401
from pipeline import avatar_routes  # noqa: F401
