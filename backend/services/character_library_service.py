"""
Character Library Service
Manages character libraries for projects
"""
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class CharacterLibraryService:
    """Service for managing project character libraries"""
    
    @staticmethod
    def extract_character_info(avatar: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and simplify character information from avatar
        
        Args:
            avatar: Avatar object with prompt, name, etc
        
        Returns:
            Simplified character dict with key information
        """
        name = avatar.get("name", "")
        prompt = avatar.get("prompt", "")
        
        # Remove "Biblizoo Baby" suffix and clean name
        clean_name = (name
            .replace(" Biblizoo Baby", "")
            .replace(" Baby", "")
            .replace("Biblizoo", "")
            .strip())
        
        # Extract animal from prompt (simple heuristic)
        animal = "Unknown"
        if "render of" in prompt:
            try:
                # Extract text between "render of" and first comma
                animal_part = prompt.split("render of")[1].split(",")[0].strip()
                # Remove the name from the animal part
                animal = animal_part.replace(clean_name, "").replace("Biblizoo", "").strip()
            except:
                pass
        
        # Extract key traits (first 150 chars after description)
        traits = ""
        if len(prompt) > 200:
            traits = prompt[100:250].strip()
        
        # Determine category (simple heuristic based on name)
        # In the future, this could be smarter
        category = "principal"  # default
        
        return {
            "id": avatar.get("id"),
            "name": clean_name,
            "full_name": name,
            "animal": animal,
            "traits": traits,
            "personality": "",  # Could be extracted from prompt with LLM
            "category": category,
            "url": avatar.get("url"),
            "prompt": prompt[:200]  # Store first 200 chars for reference
        }
    
    @staticmethod
    def build_character_library(
        folder_id: str,
        folder_name: str,
        avatars: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build a complete character library from avatars
        
        Args:
            folder_id: ID of the avatar folder
            folder_name: Name of the folder
            avatars: List of avatar objects
        
        Returns:
            Character library dict ready to save in project
        """
        characters = []
        
        for avatar in avatars:
            try:
                char_info = CharacterLibraryService.extract_character_info(avatar)
                characters.append(char_info)
            except Exception as e:
                logger.warning(f"Failed to extract character info: {e}")
                continue
        
        # Extract prompt template for visual consistency
        from services.prompt_template_service import PromptTemplateService
        template_service = PromptTemplateService()
        
        # Use pre-defined template for Biblizoo Baby, or extract from folder
        if "biblizoo" in folder_name.lower() and "baby" in folder_name.lower():
            prompt_template = template_service.get_biblizoo_baby_template()
        else:
            prompt_template = template_service.extract_template_from_folder(avatars)
        
        logger.info(f"Built character library: {len(characters)} characters with template '{prompt_template.get('style')}'")
        
        return {
            "folder_id": folder_id,
            "folder_name": folder_name,
            "last_synced": datetime.now(timezone.utc).isoformat(),
            "total_characters": len(characters),
            "characters": characters,
            "prompt_template": prompt_template,  # NEW: Template for new characters
            "version": "1.1"
        }
    
    @staticmethod
    def get_characters_summary(character_library: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of characters for LLM prompts
        
        Args:
            character_library: The character library dict
        
        Returns:
            Formatted string with character descriptions
        """
        if not character_library:
            return "Nenhum personagem pré-criado disponível."
        
        characters = character_library.get("characters", [])
        folder_name = character_library.get("folder_name", "Biblioteca")
        
        summary = f"\n📚 PERSONAGENS PRÉ-CRIADOS ({len(characters)} personagens da pasta '{folder_name}'):\n\n"
        
        # Group by category
        principals = [c for c in characters if c.get("category") == "principal"]
        others = [c for c in characters if c.get("category") != "principal"]
        
        if principals:
            summary += "PERSONAGENS PRINCIPAIS:\n"
            for char in principals[:15]:  # Limit to avoid token overflow
                summary += f"- {char['name']} ({char['animal']})\n"
            if len(principals) > 15:
                summary += f"  ... e mais {len(principals) - 15} personagens\n"
            summary += "\n"
        
        if others:
            summary += "PERSONAGENS SECUNDÁRIOS:\n"
            for char in others[:10]:
                summary += f"- {char['name']} ({char['animal']})\n"
            if len(others) > 10:
                summary += f"  ... e mais {len(others) - 10} personagens\n"
        
        return summary
    
    @staticmethod
    def format_for_llm_prompt(character_library: Dict[str, Any]) -> str:
        """
        Format character library for LLM - SIMPLIFIED for maximum clarity
        """
        if not character_library:
            return ""
        
        folder_name = character_library.get("folder_name", "Character Library")
        characters = character_library.get("characters", [])
        
        if not characters:
            return ""
        
        # ULTRA SIMPLIFIED FORMAT - Just the essentials
        instructions = f"""
═══════════════════════════════════════════════════════════════════════════════
📚 CHARACTER LIBRARY: {folder_name}
═══════════════════════════════════════════════════════════════════════════════

YOU HAVE {len(characters)} PRE-EXISTING CHARACTERS. USE THEM!

"""
        
        # List first 30 characters (simple format)
        for i, char in enumerate(characters[:30], 1):
            full_name = char.get("full_name", char.get("name", "Unknown"))
            char_id = char.get("id", "")
            animal = char.get("animal", "")
            prompt = char.get("prompt", "")[:120]
            
            instructions += f'{i}. ID: "{char_id}" | NAME: "{full_name}" | ANIMAL: {animal}\n'
            instructions += f'   PROMPT: {prompt}...\n\n'
        
        if len(characters) > 30:
            instructions += f"... and {len(characters) - 30} more characters available.\n\n"
        
        instructions += f"""
═══════════════════════════════════════════════════════════════════════════════
🎯 MANDATORY INSTRUCTIONS:
═══════════════════════════════════════════════════════════════════════════════

When you see a character name in the user's request (like "Abraão", "Isaac", "Noé"):
1. FIND IT in the list above
2. USE THE EXACT FULL NAME (with "Biblizoo Baby" suffix)
3. COPY THE ID
4. COPY THE FIRST 120 CHARS OF THE PROMPT as description

EXAMPLE - If user asks for "Abraão":
✅ CORRECT JSON:
{{
  "id": "[copy ID from list above]",
  "name": "[copy FULL NAME from list above]", 
  "description": "[copy first 120 chars of PROMPT from list above]"
}}

❌ WRONG: Creating "Abraão" without ID
❌ WRONG: Creating "Abraão" with new description
❌ WRONG: Not using "Biblizoo Baby" suffix

═══════════════════════════════════════════════════════════════════════════════
"""
        return instructions
