"""
Content Advisors System
Specialized agents that adapt content for specific audiences and formats
"""
from typing import Dict, Any, Optional
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ContentAdvisor(ABC):
    """Base class for content advisors"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    async def refine(self, content: str, config: Dict[str, Any]) -> str:
        """
        Refine content based on advisor's specialization
        
        Args:
            content: Original content to refine
            config: Configuration for this advisor
        
        Returns:
            Refined content
        """
        pass
    
    def is_enabled(self, project_config: Dict[str, Any]) -> bool:
        """Check if this advisor is enabled for the project"""
        advisors_config = project_config.get("content_advisors", {})
        advisor_config = advisors_config.get(self.name, {})
        return advisor_config.get("enabled", False)


class ToddlerContentAdvisor(ContentAdvisor):
    """
    Adapts content for children aged 2-5 years
    
    Simplifies language, adds repetition, uses concrete concepts
    """
    
    def __init__(self):
        super().__init__("toddler_content")
    
    async def refine(self, content: str, config: Dict[str, Any]) -> str:
        """
        Adapt content for 2-5 year olds
        
        Features:
        - Simple vocabulary (200-500 words)
        - Short sentences (max 8 words)
        - Repetition for learning
        - Rhetorical questions
        - Concrete concepts only
        """
        from core.llm import get_claude_client
        
        repetition_freq = config.get("repetition_frequency", "high")
        
        prompt = f"""Você é um especialista em desenvolvimento infantil para crianças de 2-5 anos.

TEXTO ORIGINAL:
{content}

ADAPTE o texto seguindo estas REGRAS IMPORTANTES:

1. **Vocabulário Simples** (200-500 palavras básicas)
   - Use palavras que crianças de 2-5 anos conhecem
   - Evite termos abstratos ou complexos

2. **Frases Curtas** (máximo 6-8 palavras)
   - Uma ideia por frase
   - Sujeito + verbo + objeto simples

3. **Repetição para Fixação** ({repetition_freq})
   - Use perguntas e respostas: "Quem é...? ... é...!"
   - Repita conceitos-chave 2-3 vezes
   - Exemplo: "Abraão é papai. Papai Abraão ama Deus. Deus ama papai Abraão!"

4. **Perguntas Retóricas** (engajamento)
   - "Quem é forte? O leão é forte!"
   - "O que faz o elefante? O elefante come!"

5. **Conceitos Concretos**
   - Evite abstrações (fé, amor abstrato)
   - Use ações visíveis: "Abraão abraça Isaque"

6. **Ritmo e Musicalidade**
   - Aliterações suaves
   - Rimas simples quando possível

EXEMPLO DE ADAPTAÇÃO:

Original: "Abraão era um homem de grande fé que confiava plenamente em Deus"

Adaptado: "Quem é Abraão? Abraão é papai!
Abraão ama Deus muito muito!
Deus fala: 'Oi Abraão!'
Abraão escuta Deus.
Abraão é feliz!"

Agora adapte o texto acima mantendo a história, mas tornando-a perfeita para crianças de 2-5 anos:
"""
        
        try:
            claude = get_claude_client()
            response = await claude.messages_create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            adapted_text = response.content[0].text
            logger.info(f"Toddler advisor: Adapted {len(content)} chars -> {len(adapted_text)} chars")
            
            return adapted_text
            
        except Exception as e:
            logger.error(f"Toddler advisor failed: {e}")
            return content  # Return original if fails


class MusicalComposerAdvisor(ContentAdvisor):
    """
    Transforms story into a catchy children's song
    
    Creates verse, chorus, bridge structure with repetitive melody
    """
    
    def __init__(self):
        super().__init__("musical_composer")
    
    async def refine(self, content: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform story into musical format
        
        Returns dict with:
        - lyrics: Full lyrics with structure markers
        - style: Music style description
        - duration: Target duration in seconds
        """
        from core.llm import get_claude_client
        
        music_style = config.get("music_style", "chiclete")
        
        prompt = f"""Você é um compositor especializado em MÚSICAS INFANTIS CHICLETE (grudentas e memoráveis).

HISTÓRIA ORIGINAL:
{content}

TRANSFORME em uma MÚSICA INFANTIL EDUCATIVA com:

1. **REFRÃO CATIVANTE** (4-6 linhas)
   - Extremamente repetitivo e fácil de memorizar
   - Usa o nome dos personagens principais
   - Melodia simples que "gruda na cabeça"
   - Exemplo: "♪ Abraão, Abraão, papai de Isaque! / Isaque, Isaque, filho do papai! ♪"

2. **VERSOS SIMPLES** (2-3 versos de 4-6 linhas cada)
   - Contam a história de forma clara
   - Palavras que rimam naturalmente
   - Uma ideia por verso

3. **ESTRUTURA**:
   [Refrão]
   (refrão cativante)
   
   [Verso 1]
   (primeira parte da história)
   
   [Refrão]
   
   [Verso 2]
   (continuação da história)
   
   [Refrão]

4. **CARACTERÍSTICAS**:
   - Aliterações e rimas
   - Repetição de palavras-chave
   - Ritmo alegre e pulsante
   - Sons onomatopaicos (la la, na na)
   - Fácil de cantar junto

5. **ESTILO MUSICAL**: {music_style}
   - Instrumentos: xilofone, tambor, pandeiro, flauta
   - Tom: alegre, educativo, divertido
   - BPM: moderado (120-140)

EXEMPLO:

[Refrão]
♪ Noé, Noé, construiu um barco grande!
♪ Chuva, chuva, água por todo lugar!
♪ Animais, animais, todos vão entrar!
♪ Lalala lalala, Noé vai nos salvar! ♪

[Verso 1]
Noé trabalha, martelando o barco
Dois por dois, os bichinhos chegando
Leão e leoa, elefante e passarinho
Todos juntos cantando bem baixinho!

[Refrão]
♪ Noé, Noé, construiu um barco grande!
...

Agora transforme a história acima em uma música chiclete:
"""
        
        try:
            claude = get_claude_client()
            response = await claude.messages_create(
                model="claude-sonnet-4-20250514",
                max_tokens=3000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            lyrics = response.content[0].text
            
            # Extract style description for music generation
            style_description = (
                f"upbeat children's music, {music_style}, catchy chorus, "
                f"xylophone, tambourine, cheerful, educational, sing-along"
            )
            
            logger.info(f"Musical composer: Created lyrics ({len(lyrics)} chars)")
            
            # Extract scene suggestions for video
            scene_suggestions = self._extract_scene_suggestions(lyrics, content)
            
            return {
                "lyrics": lyrics,
                "style": style_description,
                "duration": 180,  # 3 minutes
                "structure": "chorus-verse-chorus-verse-chorus",
                "video_scenes": scene_suggestions  # For music video generation
            }
            
        except Exception as e:
            logger.error(f"Musical composer failed: {e}")
            return {
                "lyrics": content,
                "style": "children's music",
                "duration": 180,
                "video_scenes": []
            }
    
    def _extract_scene_suggestions(self, lyrics: str, original_story: str) -> list:
        """
        Extract visual scene suggestions from lyrics and story
        
        Args:
            lyrics: Generated song lyrics
            original_story: Original story text
        
        Returns:
            List of scene descriptions for video generation
        """
        # Split lyrics into verses
        parts = lyrics.split('[')
        scenes = []
        
        for part in parts:
            if 'Verso' in part or 'Verse' in part:
                # Extract verse content
                if ']' in part:
                    verse_text = part.split(']', 1)[1].strip()
                    if verse_text:
                        # Create scene description
                        scene = {
                            "type": "verse",
                            "description": f"Characters in joyful activities: {verse_text[:100]}...",
                            "action": "dancing, playing, moving rhythmically"
                        }
                        scenes.append(scene)
            elif 'Refrão' in part or 'Chorus' in part:
                if ']' in part:
                    chorus_text = part.split(']', 1)[1].strip()
                    if chorus_text:
                        scene = {
                            "type": "chorus",
                            "description": f"Energetic celebration: {chorus_text[:100]}...",
                            "action": "jumping, spinning, celebrating together"
                        }
                        scenes.append(scene)
        
        # If no verses/chorus detected, create generic scenes
        if not scenes:
            scenes = [
                {
                    "type": "intro",
                    "description": "Characters introduction in colorful environment",
                    "action": "waving, smiling, dancing gently"
                },
                {
                    "type": "main",
                    "description": "Characters playing and having fun together",
                    "action": "running, jumping, laughing joyfully"
                },
                {
                    "type": "outro",
                    "description": "Characters celebrating happily",
                    "action": "dancing in circle, clapping hands"
                }
            ]
        
        return scenes


class NarrationStyleAdvisor(ContentAdvisor):
    """
    Adds narration style markers for voice synthesis
    
    Defines tone, pauses, emphasis for dramatic effect
    """
    
    def __init__(self):
        super().__init__("narration_style")
    
    async def refine(self, content: str, config: Dict[str, Any]) -> str:
        """
        Add narration markers to content
        
        Adds:
        - [PAUSA] for dramatic pauses
        - [ENFASE: palavra] for emphasis
        - [TOM: entusiasmado/calmo/misterioso] for tone changes
        """
        from core.llm import get_claude_client
        
        tone = config.get("tone", "enthusiastic")
        voice_guidance = config.get("voice_guidance", True)
        
        if not voice_guidance:
            return content
        
        prompt = f"""Você é um diretor de narração para conteúdo infantil.

TEXTO ORIGINAL:
{content}

ADICIONE marcações de narração para tornar a leitura mais DRAMÁTICA e ENVOLVENTE para crianças.

MARCAÇÕES DISPONÍVEIS:

1. **[PAUSA]** - Pausa dramática (1-2 segundos)
   Use antes de revelações, momentos importantes

2. **[ENFASE: palavra]** - Enfatizar palavra específica
   Use em palavras-chave, nomes, ações importantes

3. **[TOM: tipo]** - Mudar tom de voz
   Tipos: entusiasmado, calmo, misterioso, suave, animado
   Use para mudanças de emoção na história

4. **[VELOCIDADE: tipo]** - Ritmo de fala
   Tipos: rápido, normal, lento
   Use para criar tensão ou relaxamento

TOM PRINCIPAL: {tone}

EXEMPLO:

Original: "Abraão olhou para o céu. Deus falou com ele. 'Abraão, você confia em mim?'"

Com marcações: "[TOM: calmo] Abraão olhou para o [ENFASE: céu]. [PAUSA] [TOM: misterioso] Deus falou com ele. [PAUSA] [TOM: suave] 'Abraão, você [ENFASE: confia] em mim?'"

Adicione marcações ao texto acima:
"""
        
        try:
            claude = get_claude_client()
            response = await claude.messages_create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            marked_text = response.content[0].text
            logger.info("Narration advisor: Added style markers")
            
            return marked_text
            
        except Exception as e:
            logger.error(f"Narration advisor failed: {e}")
            return content


# Factory function
def get_advisor(advisor_type: str) -> Optional[ContentAdvisor]:
    """Get advisor instance by type"""
    advisors = {
        "toddler_content": ToddlerContentAdvisor,
        "musical_composer": MusicalComposerAdvisor,
        "narration_style": NarrationStyleAdvisor
    }
    
    advisor_class = advisors.get(advisor_type)
    if advisor_class:
        return advisor_class()
    return None
