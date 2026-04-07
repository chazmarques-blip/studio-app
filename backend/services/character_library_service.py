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
        
        return {
            "folder_id": folder_id,
            "folder_name": folder_name,
            "last_synced": datetime.now(timezone.utc).isoformat(),
            "total_characters": len(characters),
            "characters": characters,
            "version": "1.0"
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
        Format character library for inclusion in LLM prompts
        
        Args:
            character_library: The character library dict
        
        Returns:
            Formatted instructions for LLM
        """
        if not character_library:
            return ""
        
        summary = CharacterLibraryService.get_characters_summary(character_library)
        
        instructions = f"""
{summary}

📋 REGRAS IMPORTANTES PARA USO DE PERSONAGENS:

1. **USE PRIORITARIAMENTE** os personagens listados acima
   - Eles já estão criados e prontos para uso
   - Mantenha consistência com suas características

2. **Crie novos personagens APENAS se absolutamente necessário**
   - Exemplo: figurantes, extras, personagens únicos da história
   - Quando criar, indique claramente: "NOVO PERSONAGEM: [nome] - [descrição]"

3. **Mantenha a essência dos personagens existentes**
   - Respeite suas personalidades e características visuais
   - Use os nomes exatamente como listados

"""
        return instructions
