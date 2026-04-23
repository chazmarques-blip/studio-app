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
from . import continuity_audit  # Video (Thelma) + Book visual (Glen Keane) continuity
from . import book_editable  # Quality gate + editable spreads JSON + regenerate image
from . import agents_activity  # NEW — real-time "active agent" tracker for UI feedback
from . import agents_metrics  # NEW — aggregate metrics (activations, cost, latency)
from . import multi_format_export  # NEW — 9:16/1:1/4:5 reformat exports
from . import cost_estimator
from . import dialogue_timeline  # NEW
from . import cinematography  # NEW
from . import migration  # NEW
from . import scene_reorder  # NEW
from . import scene_regenerate  # NEW - Scene regeneration
from . import kling_storyboard  # NEW - Kling 30-frame storyboards
from . import sora_characters  # NEW - Sora 2 Characters API for voice/appearance consistency
from . import book_factory  # NEW - BookFactory: parallel book generation pipeline (WeasyPrint)

__all__ = ["router", "_cleanup_stale_storyboards"]
