# Criação em Lote - Guia de Uso com Prompts Completos

## Como Separar Prompts

**Método:** Use **linha em branco** entre cada prompt

### ✅ Formato Correto

```
chibi 3D render of Urso Macho Biblizoo Baby, wild male brown bear, quadruped natural standing pose on four legs, realistic animal body proportions...

chibi 3D render of Girafa Fêmea Biblizoo Baby, gentle female giraffe, quadruped natural standing pose, long elegant neck naturally proportional...

chibi 3D render of Leão Biblizoo Baby, brave young male lion, quadruped natural standing pose, golden yellow-orange mane beginning to grow...
```

**Explicação:**
- Prompt 1 (completo)
- [LINHA EM BRANCO]
- Prompt 2 (completo)
- [LINHA EM BRANCO]
- Prompt 3 (completo)

## Exemplo com Seu Prompt

```
chibi 3D render of Urso Macho Biblizoo Baby, wild male brown bear, quadruped natural standing pose on four legs, realistic animal body proportions and anatomy, broad rounded head naturally proportional to stocky body, moderately large warm dark honey-brown round eyes with natural wild animal light reflection and very subtle cute sparkle, natural rich warm chestnut-brown fur with realistic thick dense texture detail and very subtle softness, broad strong paws with natural claws, very subtle rosy blush on cheeks, subtle vibrant accent: bright coral-orange inner ear lining only, realistic stocky legs and short fluffy tail, bold friendly confident baby animal expression, NO oversized head, NO chibi head proportions, NO clothing, NO accessories, NO bipedal pose, same cartoon 3D render style as BibleZoo characters but with more realistic animal proportions, ultra-vibrant saturated colors on fur, clean white background, soft warm studio lighting, child-friendly, ultra-detailed, 4k --ar 3:2 --v 6 --style raw --q 2

chibi 3D render of Elefante Macho Biblizoo Baby, young male elephant, quadruped natural standing pose, large ears, long trunk, gentle eyes, gray skin...

chibi 3D render of Tigre Macho Biblizoo Baby, striped orange and black tiger cub, crouching pose, bright amber eyes, fierce but cute expression...
```

## ❌ Formato INCORRETO

```
Urso Macho Biblizoo Baby
Girafa Fêmea Biblizoo Baby
Leão Biblizoo Baby
```
**Problema:** Prompts muito curtos + não tem linha em branco

## Como Testar

1. Abra o modal "Criar Personagem"
2. Clique em "Por Prompt" → "Em Lote"
3. Cole 2-3 prompts completos separados por linha em branco
4. Veja o contador: "3 personagens serão criados"
5. Clique em "Gerar Todos"

## Dicas

- ✅ Cada prompt pode ter múltiplas linhas de descrição
- ✅ Prompts complexos com parâmetros Midjourney funcionam
- ✅ O sistema detecta automaticamente o nome do personagem
- ✅ Auto-assignment de pastas baseado no nome
- ⚠️ Máximo 20 prompts por lote
- ⚠️ Tempo: ~3-5s por personagem

## Detecção de Nome

O sistema tenta extrair o nome automaticamente:

**Padrão 1:** "chibi 3D render of **Urso Macho Biblizoo Baby**, description..."
→ Nome: "Urso Macho Biblizoo Baby"

**Padrão 2:** "**Nome do Personagem**, description..."
→ Nome: "Nome do Personagem"

**Fallback:** Primeiras 30 caracteres do prompt
