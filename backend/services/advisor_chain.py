"""
Advisor Chain System
Executes multiple content advisors in sequence to adapt screenplay content
"""
from typing import Dict, Any, List, Optional
import logging
from services.content_advisors import (
    ContentAdvisor,
    ToddlerContentAdvisor,
    MusicalComposerAdvisor,
    NarrationStyleAdvisor,
    get_advisor
)

logger = logging.getLogger(__name__)


class AdvisorChain:
    """
    Executes multiple advisors in sequence
    
    Each advisor can modify the content based on its specialization
    Results are saved at each step for comparison and rollback
    """
    
    def __init__(self, advisors: List[ContentAdvisor] = None):
        """
        Initialize advisor chain
        
        Args:
            advisors: List of advisor instances. If None, uses default advisors
        """
        if advisors is None:
            advisors = [
                ToddlerContentAdvisor(),
                MusicalComposerAdvisor(),
                NarrationStyleAdvisor()
            ]
        self.advisors = advisors
    
    async def process(self, content: str, project_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process content through all enabled advisors
        
        Args:
            content: Original content to process
            project_config: Project configuration containing content_advisors settings
        
        Returns:
            Dictionary with:
            - original: Original content
            - final: Final processed content
            - stages: Dict mapping advisor names to their output
            - applied_advisors: List of advisor names that were applied
        """
        results = {
            "original": content,
            "stages": {},
            "applied_advisors": []
        }
        
        current_content = content
        
        for advisor in self.advisors:
            if advisor.is_enabled(project_config):
                try:
                    logger.info(f"Applying advisor: {advisor.name}")
                    
                    # Get advisor config
                    advisors_config = project_config.get("content_advisors", {})
                    advisor_config = advisors_config.get(advisor.name, {})
                    
                    # Process content
                    processed = await advisor.refine(current_content, advisor_config)
                    
                    # Save result
                    results["stages"][advisor.name] = processed
                    results["applied_advisors"].append(advisor.name)
                    
                    # Update current content for next advisor
                    current_content = processed
                    
                    logger.info(f"Advisor {advisor.name} completed successfully")
                    
                except Exception as e:
                    logger.error(f"Advisor {advisor.name} failed: {e}")
                    # Continue with next advisor on error
                    results["stages"][advisor.name] = {"error": str(e), "content": current_content}
            else:
                logger.debug(f"Advisor {advisor.name} is disabled, skipping")
        
        results["final"] = current_content
        
        logger.info(f"Advisor chain complete. Applied {len(results['applied_advisors'])} advisors: {results['applied_advisors']}")
        
        return results
    
    @staticmethod
    async def process_screenplay(
        screenplay_text: str,
        project_config: Dict[str, Any],
        advisor_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Convenience method to process screenplay with specific advisors
        
        Args:
            screenplay_text: Complete screenplay text to process
            project_config: Project configuration
            advisor_types: List of advisor type names (e.g., ["toddler_content", "musical_composer"])
                          If None, uses all available advisors
        
        Returns:
            Processing results from advisor chain
        """
        if advisor_types:
            advisors = [get_advisor(advisor_type) for advisor_type in advisor_types]
            advisors = [a for a in advisors if a is not None]
        else:
            advisors = None
        
        chain = AdvisorChain(advisors)
        return await chain.process(screenplay_text, project_config)


# Helper function to check if any advisor is enabled
def has_active_advisors(project_config: Dict[str, Any]) -> bool:
    """
    Check if any content advisor is enabled in project config
    
    Args:
        project_config: Project configuration
    
    Returns:
        True if at least one advisor is enabled
    """
    advisors_config = project_config.get("content_advisors", {})
    if not advisors_config:
        return False
    
    for advisor_name, config in advisors_config.items():
        if isinstance(config, dict) and config.get("enabled", False):
            return True
    
    return False


# Helper to get default config for a project type
def get_default_advisor_config(project_type: str = "toddler") -> Dict[str, Any]:
    """
    Get default content advisor configuration for a project type
    
    Args:
        project_type: Type of project ("toddler", "musical", "narrated", etc.)
    
    Returns:
        Default configuration dictionary
    """
    configs = {
        "toddler": {
            "toddler_content": {
                "enabled": True,
                "vocabulary_level": "simple",
                "repetition_frequency": "high"
            },
            "musical_composer": {
                "enabled": False
            },
            "narration_style": {
                "enabled": True,
                "tone": "enthusiastic",
                "voice_guidance": True
            }
        },
        "musical": {
            "toddler_content": {
                "enabled": False
            },
            "musical_composer": {
                "enabled": True,
                "music_style": "chiclete",
                "duration_target": "2-3min"
            },
            "narration_style": {
                "enabled": False
            }
        },
        "narrated": {
            "toddler_content": {
                "enabled": False
            },
            "musical_composer": {
                "enabled": False
            },
            "narration_style": {
                "enabled": True,
                "tone": "calm",
                "voice_guidance": True
            }
        },
        "default": {
            "toddler_content": {
                "enabled": False
            },
            "musical_composer": {
                "enabled": False
            },
            "narration_style": {
                "enabled": False
            }
        }
    }
    
    return configs.get(project_type, configs["default"])
