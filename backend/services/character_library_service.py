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
        
        Returns detailed character info including ORIGINAL prompts
        """
        if not character_library:
            return ""
        
        folder_name = character_library.get("folder_name", "Character Library")
        characters = character_library.get("characters", [])
        
        if not characters:
            return ""
        
        instructions = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 BIBLIOTECA DE PERSONAGENS DISPONÍVEIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Você tem acesso a {len(characters)} personagens PRÉ-CRIADOS da pasta "{folder_name}".

⚠️ REGRA CRÍTICA DE CONTINUIDADE:
Você DEVE usar EXATAMENTE estes personagens quando a história envolver seus nomes.
NÃO crie novos personagens se eles já existem aqui.
USE o nome completo e a descrição EXATA fornecida.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PERSONAGENS DISPONÍVEIS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
        
        # Show detailed info for first 20 characters (to avoid token overflow)
        for i, char in enumerate(characters[:20], 1):
            full_name = char.get("full_name", char.get("name", "Unknown"))
            animal = char.get("animal", "Unknown")
            prompt_preview = char.get("prompt", "")[:150]
            
            instructions += f"{i}. **{full_name}**\n"
            instructions += f"   Animal: {animal}\n"
            instructions += f"   Descrição: {prompt_preview}...\n"
            instructions += f"   ID: {char.get('id')}\n\n"
        
        if len(characters) > 20:
            instructions += f"\n... e mais {len(characters) - 20} personagens disponíveis.\n\n"
        
        instructions += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 INSTRUÇÕES DE USO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. **SEMPRE consulte esta lista ANTES de criar a história**
   - Se o usuário pedir "história sobre Abraão", use "Abraão Biblizoo Baby" desta lista
   - USE o nome COMPLETO exatamente como aparece (ex: "Abraão Biblizoo Baby")

2. **NO campo "characters" do JSON:**
   - Inclua o ID do personagem: {{"id": "abc123", "name": "Abraão Biblizoo Baby"}}
   - Mantenha a descrição ORIGINAL (os primeiros 150 caracteres do prompt)

3. **NÃO crie novos prompts para personagens existentes**
   - ❌ ERRADO: Criar "Abraão - carneiro idoso com..."
   - ✅ CORRETO: Usar "Abraão Biblizoo Baby" com ID e descrição original

4. **Crie novos personagens APENAS se:**
   - Não existirem nesta biblioteca
   - Forem figurantes/extras específicos da história
   - Nesse caso, marque claramente: "name": "NOVO: [Nome]"

5. **Para continuidade visual:**
   - Personagens com ID garantem mesma aparência em todos os vídeos
   - É ESSENCIAL para séries e conteúdo recorrente

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return instructions
