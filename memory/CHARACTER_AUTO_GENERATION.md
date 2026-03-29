# Geração Automática de Personagens - StudioX

## 📋 Funcionalidade Implementada

Geração automática de imagens para TODOS os personagens quando o usuário entra na etapa "PERSONAGENS" (Step 2).

## 🎯 Comportamento

### Fluxo Automático
1. **Detecção**: Ao entrar no Step 2, o sistema detecta personagens sem avatar
2. **Verificação de Acervo**: Antes de gerar, verifica se existe personagem com mesmo nome no acervo global
3. **Reutilização**: Se encontrado no acervo, aplica automaticamente (economiza custo)
4. **Geração**: Para personagens não encontrados, gera imagem via Gemini (imagen-3.0-generate-002)
5. **Aplicação**: Imagens são automaticamente aplicadas aos personagens
6. **Notificação**: Mostra resumo: "✨ 3 personagens gerados, 2 reutilizados do acervo!"

### Especificações de Imagem
Todas as imagens geradas seguem o padrão:
- ✅ Personagem de frente (facing front)
- ✅ Fundo transparente (transparent background)
- ✅ Full body portrait
- ✅ Character reference sheet quality
- ✅ Estilo visual do projeto (Pixar 3D, Realistic, Anime, etc.)

## 🔧 Implementação Técnica

### Backend
**Endpoint**: `POST /api/studio/projects/{project_id}/characters/generate-all`

**Resposta**:
```json
{
  "total": 5,
  "generated": 3,
  "reused": 2,
  "failed": 0,
  "characters": [
    {
      "name": "Pomba da Paz",
      "status": "generated",
      "avatar_url": "https://...",
      "avatar_id": "abc123"
    },
    {
      "name": "Sol Sorridente",
      "status": "reused",
      "avatar_url": "https://...",
      "avatar_id": "def456"
    }
  ]
}
```

### Frontend
**Hook**: `useEffect` no Step 2 dispara geração automaticamente

**Estados**:
- `autoGenCharacters`: Boolean - Indica se geração está em andamento
- `charGenProgress`: Object - Status e progresso da geração

**Componentes**:
- Loading overlay com animação durante geração
- Botão de fallback "🎨 Gerar Todos os Personagens Faltantes" (caso auto-gen falhe)

## 📦 Armazenamento

### Projeto Local
Personagens são salvos em:
- `project.project_avatars[]` - Lista de avatares do projeto
- `project.character_avatars{}` - Mapa {nome_personagem: url_avatar}

### Acervo Global
Personagens também são salvos no acervo global (`studio_avatars`) para reutilização futura entre projetos.

## 🔄 Reutilização de Personagens

O sistema verifica se existe um personagem com o **mesmo nome** no acervo global antes de gerar:

```python
existing_global = next(
    (a for a in global_avatars if a.get("name", "").lower() == char_name.lower()), 
    None
)
```

Se encontrado, reutiliza automaticamente - economizando:
- ⏱️ Tempo de geração
- 💰 Custo de API (Gemini)
- 🎨 Consistência visual entre projetos

## 🎨 Prompts de Geração

Exemplo de prompt construído:
```
[Descrição do personagem]

Pixar 3D animation style, high quality CGI render

CRITICAL REQUIREMENTS:
- Character facing FRONT (looking directly at camera)
- TRANSPARENT background (no background elements)
- Full body portrait visible
- Character reference sheet quality
- Sharp details, well-lit, neutral standing pose
```

## 🔍 Casos de Uso

### Caso 1: Projeto Novo
1. Usuário cria roteiro com 5 personagens
2. Avança para Step 2 (Personagens)
3. Sistema detecta 5 personagens sem avatar
4. Verifica acervo: 0 encontrados
5. Gera automaticamente 5 imagens
6. Aplica e salva no projeto + acervo global

### Caso 2: Projeto com Continuidade
1. Usuário cria novo roteiro com "Pomba da Paz" (já usado em projeto anterior)
2. Avança para Step 2
3. Sistema detecta 1 personagem sem avatar
4. Verifica acervo: 1 encontrado (Pomba da Paz)
5. Reutiliza imagem existente (instantâneo)
6. Notifica: "1 personagem reutilizado do acervo!"

### Caso 3: Falha na Geração
1. Geração automática falha (API error, network issue)
2. Sistema exibe botão de fallback
3. Usuário clica em "🎨 Gerar Todos os Personagens Faltantes"
4. Processo reinicia manualmente

## 📊 Vantagens

✅ **Zero fricção**: Usuário não precisa clicar em nada, geração é automática
✅ **Consistência**: Todos os personagens seguem mesmo padrão visual
✅ **Economia**: Reutiliza personagens entre projetos
✅ **Velocidade**: Geração em batch (paralela)
✅ **Fallback**: Botão manual caso auto-gen falhe

## 🧪 Teste Manual

1. Login: `test@studiox.com` / `studiox123`
2. Criar novo projeto
3. Escrever roteiro com personagens
4. Aprovar roteiro e avançar para Step 2
5. **Observar**: Geração automática inicia
6. **Resultado**: Personagens aparecem com imagens aplicadas

## 🐛 Troubleshooting

### Geração não inicia
- Verificar: `characters.length > 0`
- Verificar: `characterAvatars[char.name]` vazio para pelo menos 1 personagem
- Checar logs: `/var/log/supervisor/backend.err.log`

### Imagens não aparecem
- Verificar URL do Supabase Storage
- Checar permissões do bucket `studiox`
- Verificar `GEMINI_API_KEY` em `/app/backend/.env`

### Erro "coroutine not awaited"
- Confirmar: `await gen.generate_images()` no backend
- Reiniciar backend: `sudo supervisorctl restart backend`
