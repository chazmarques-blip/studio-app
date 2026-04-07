"""
Prompt Template Service
Extracts and applies visual style templates from character folders
"""
from typing import Dict, List, Any, Optional
import re
import logging

logger = logging.getLogger(__name__)


class PromptTemplateService:
    """
    Service for managing prompt templates and visual style consistency
    
    Extracts common patterns from existing character prompts
    and applies them to new characters for visual consistency
    """
    
    @staticmethod
    def extract_template_from_folder(avatars: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract common prompt template from a folder of avatars
        
        Analyzes existing prompts to find common patterns:
        - Style keywords (chibi, 3D, render, etc.)
        - Pose instructions
        - Visual characteristics (eyes, head size, etc.)
        - Quality markers (4k, ultra-detailed, etc.)
        
        Args:
            avatars: List of avatar objects with prompts
        
        Returns:
            Template dict with extracted patterns
        """
        if not avatars:
            return {"style": "default", "template": "", "keywords": []}
        
        prompts = [a.get("prompt", "") for a in avatars if a.get("prompt")]
        
        if not prompts:
            return {"style": "default", "template": "", "keywords": []}
        
        # Analyze first 5 prompts to find patterns
        sample_prompts = prompts[:5]
        
        # Common Biblizoo Baby patterns
        common_keywords = []
        patterns = {
            "style_prefix": "",
            "pose": "",
            "eyes": "",
            "head_size": "",
            "quality_suffix": "",
            "background": "",
        }
        
        # Extract style prefix (before character name)
        # Example: "chibi 3D render of"
        for prompt in sample_prompts:
            if "render of" in prompt.lower():
                prefix = prompt.split("render of")[0].strip() + " render of"
                patterns["style_prefix"] = prefix
                break
        
        # Extract pose instructions
        if any("front-facing standing pose" in p for p in sample_prompts):
            patterns["pose"] = "front-facing standing pose"
        elif any("standing pose" in p for p in sample_prompts):
            patterns["pose"] = "standing pose"
        
        # Extract eyes pattern
        if any("huge shiny" in p and "round eyes" in p for p in sample_prompts):
            patterns["eyes"] = "huge shiny [COLOR] round eyes with light reflection"
        
        # Extract head size
        if any("oversized round head" in p for p in sample_prompts):
            patterns["head_size"] = "oversized round head 50% of body height"
        elif any("large head" in p for p in sample_prompts):
            patterns["head_size"] = "large head"
        
        # Extract quality markers
        for prompt in sample_prompts:
            if "4k" in prompt.lower():
                patterns["quality_suffix"] = "ultra-detailed, 4k"
                break
            elif "ultra-detailed" in prompt.lower():
                patterns["quality_suffix"] = "ultra-detailed"
                break
        
        # Extract background
        if any("clean white background" in p for p in sample_prompts):
            patterns["background"] = "clean white background, soft warm studio lighting"
        
        # Build template
        template_parts = []
        
        if patterns["style_prefix"]:
            template_parts.append(patterns["style_prefix"] + " [NAME] Biblizoo, [ANIMAL]")
        
        if patterns["pose"]:
            template_parts.append(patterns["pose"])
        
        if patterns["eyes"]:
            template_parts.append(patterns["eyes"])
        
        if patterns["head_size"]:
            template_parts.append(patterns["head_size"])
        
        template_parts.append("[VISUAL_CHARACTERISTICS]")
        
        if patterns["background"]:
            template_parts.append(patterns["background"])
        
        if patterns["quality_suffix"]:
            template_parts.append(patterns["quality_suffix"])
        
        template = ", ".join(template_parts)
        
        # Extract common keywords
        all_text = " ".join(sample_prompts).lower()
        keyword_candidates = ["chibi", "3d", "render", "vivid", "cute", "cartoon", 
                             "stylized", "colorful", "children", "friendly"]
        common_keywords = [kw for kw in keyword_candidates if kw in all_text]
        
        logger.info(f"Extracted template from {len(avatars)} avatars: {template[:100]}...")
        
        return {
            "style": "biblizoo_baby" if "biblizoo" in all_text else "custom",
            "template": template,
            "patterns": patterns,
            "keywords": common_keywords,
            "sample_count": len(sample_prompts)
        }
    
    @staticmethod
    def apply_template_to_new_character(
        template: Dict[str, Any],
        character_name: str,
        animal: str,
        visual_characteristics: str,
        eye_color: str = "warm brown"
    ) -> str:
        """
        Apply template to new character to maintain visual consistency
        
        Args:
            template: Template dict from extract_template_from_folder
            character_name: Name of new character
            animal: Animal type (sheep, deer, lion, etc.)
            visual_characteristics: Specific visual traits
            eye_color: Eye color for the character
        
        Returns:
            Complete prompt following the template style
        """
        template_str = template.get("template", "")
        
        if not template_str:
            # Fallback to simple prompt
            return f"{character_name}, {animal}, {visual_characteristics}"
        
        # Replace placeholders
        prompt = template_str
        prompt = prompt.replace("[NAME]", character_name)
        prompt = prompt.replace("[ANIMAL]", animal)
        prompt = prompt.replace("[COLOR]", eye_color)
        prompt = prompt.replace("[VISUAL_CHARACTERISTICS]", visual_characteristics)
        
        logger.info(f"Generated prompt for new character '{character_name}' using template")
        
        return prompt
    
    @staticmethod
    def get_biblizoo_baby_template() -> Dict[str, Any]:
        """
        Get pre-defined Biblizoo Baby template
        
        Returns standard Biblizoo Baby template without needing to analyze
        """
        return {
            "style": "biblizoo_baby",
            "template": "chibi 3D render of [NAME] Biblizoo, [ANIMAL], front-facing standing pose, huge shiny [COLOR] round eyes with light reflection, oversized round head 50% of body height, VIVID [VISUAL_CHARACTERISTICS], clean white background, soft warm studio lighting, child-friendly, ultra-detailed, 4k --ar 2:3 --v 6 --style raw --q 2",
            "patterns": {
                "style_prefix": "chibi 3D render of",
                "pose": "front-facing standing pose",
                "eyes": "huge shiny [COLOR] round eyes with light reflection",
                "head_size": "oversized round head 50% of body height",
                "quality_suffix": "child-friendly, ultra-detailed, 4k --ar 2:3 --v 6 --style raw --q 2",
                "background": "clean white background, soft warm studio lighting"
            },
            "keywords": ["chibi", "3d", "render", "vivid", "cute", "friendly"],
            "sample_count": 71
        }


# Global service instance
_prompt_template_service: Optional[PromptTemplateService] = None

def get_prompt_template_service() -> PromptTemplateService:
    """Get or create the global prompt template service instance"""
    global _prompt_template_service
    if _prompt_template_service is None:
        _prompt_template_service = PromptTemplateService()
    return _prompt_template_service
