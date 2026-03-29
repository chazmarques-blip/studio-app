"""Studio package — modular split of the Directed Studio router."""
from ._shared import router, _cleanup_stale_storyboards

# Import all endpoint modules to register their routes on the shared router
from . import projects
from . import storyboard
from . import dialogues
from . import smart_edit
from . import continuity
from . import book
from . import screenwriter
from . import production
from . import narration
from . import post_production
from . import director
from . import project_bible
from . import autonomous_loop
from . import agents_registry

__all__ = ["router", "_cleanup_stale_storyboards"]
