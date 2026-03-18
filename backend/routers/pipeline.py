"""Thin wrapper that re-exports the pipeline router from the pipeline package.

The actual implementation lives in /app/backend/pipeline/ with the following modules:
- config.py: Constants, models, configuration
- utils.py: Storage, text parsing, AI utilities
- prompts.py: AI agent prompt construction
- media.py: Image and video generation/processing
- engine.py: Step execution, recovery, state management
- avatar_routes.py: Avatar API endpoints
- routes.py: Core pipeline API endpoints
"""

from pipeline import router

__all__ = ["router"]
