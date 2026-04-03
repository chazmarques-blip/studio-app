# Plano Completo: Áudio Automático + Sistema de Camadas
**Data**: 2026-04-03  
**Baseado nas respostas do usuário**

---

## 📋 **SITUAÇÃO ATUAL (Confirmada pelo Usuário)**

### ✅ **O que JÁ funciona:**
1. Vídeos **SÃO gerados com áudio automaticamente**
2. Sistema gera diálogos e sonoplastias
3. Qualidade de áudio é alta (96kHz, 192kbps)

### ❌ **Problemas Identificados:**

#### **Problema 1: Bugs de Áudio** ✅ JÁ CORRIGIDOS (Fase 1)
- ❌ Áudio não segue texto exato → ✅ CORRIGIDO (usa `scene["dialogue"]` direto)
- ❌ Mistura português e inglês → ✅ CORRIGIDO (`language_code` sempre passa)

#### **Problema 2: Funções de UI Não Funcionam** 🔴 URGENTE
- ❌ Botão "Editar" não abre
- ❌ Botão "Regenerar" não funciona
- **Causa provável**: Erro de JavaScript, modal não renderiza, ou estado travado

#### **Problema 3: Falta Sistema de Camadas** 🆕 FEATURE NOVA
- ❌ Vídeos exportados são "achatados" (todas faixas mescladas)
- ❌ Não permite edição posterior estilo CapCut
- **Solução desejada**: Salvar camadas separadas para edição posterior

---

## 🎯 **PLANO DE AÇÃO**

### **FASE 1: Bugs de Áudio** ✅ COMPLETO
- [x] Idioma consistente (ElevenLabs `language_code`)
- [x] Texto exato (sem reescrever com Claude)
- [x] Limpeza inteligente (fallback preserva original)
- **Status**: IMPLEMENTADO, aguardando teste do usuário

---

### **FASE 2: Restaurar Funções de Editar/Regenerar** 🔴 PRÓXIMO
**Prioridade**: URGENTE

#### **Investigação Necessária:**
1. ✅ Código das funções existe (`editingScene`, `regenerateScene`)
2. ❓ Por que não está abrindo?
   - Erro de JavaScript no console?
   - Modal renderiza mas não aparece (z-index)?
   - Click event não dispara?
   - Estado `editingScene` não atualiza?

#### **Plano de Correção:**
1. **Debugar Frontend**:
   ```javascript
   // Adicionar logs temporários
   onClick={() => { 
     console.log('Edit clicked, sceneNum:', sceneNum);
     setEditingScene(sceneNum); 
   }}
   ```

2. **Verificar Renderização Condicional**:
   ```javascript
   {editingScene === sceneNum && (
     <div>Form de edição</div>
   )}
   ```
   - Confirmar que `editingScene` está mudando
   - Confirmar que o form está sendo renderizado

3. **Verificar Conflitos de CSS/Z-index**:
   - Modal pode estar renderizando "atrás" de outro elemento
   - Verificar `z-index`, `position`, `overflow`

4. **Testar Endpoint de Regeneração**:
   ```bash
   curl -X POST "$API/studio/projects/{project_id}/regenerate-scene" \
     -H "Content-Type: application/json" \
     -d '{"scene_number": 1}'
   ```

#### **Arquivos para Modificar:**
- `/app/frontend/src/components/DirectedStudio.jsx` (linhas 3070-3116)
- Possível fix no CSS ou z-index

---

### **FASE 3: Sistema de Camadas para Edição** 🆕 FEATURE NOVA
**Prioridade**: IMPORTANTE (após Fase 2)

#### **Requisitos do Usuário:**
- **Automático**: Vídeos gerados automaticamente COM áudio
- **Camadas Separadas**: Salvar componentes separadamente
- **Edição Posterior**: Permitir ajuste fino em editor estilo CapCut

#### **Arquitetura Proposta:**

##### **3.1. Estrutura de Camadas**
Cada cena terá:
```json
{
  "scene_number": 1,
  "layers": {
    "video_base": "https://storage/scene_1_base.mp4",      // Vídeo Sora 2 puro (sem áudio)
    "narration": "https://storage/scene_1_narration.mp3",  // Faixa de diálogo/narração
    "music": "https://storage/scene_1_music.mp3",          // Faixa de música de fundo
    "sfx": "https://storage/scene_1_sfx.mp3",              // Efeitos sonoros (opcional)
    "final_mix": "https://storage/scene_1_final.mp4"       // Vídeo final mesclado
  },
  "timeline": {
    "narration_offset": 0.5,     // Narração começa 0.5s depois
    "music_volume": 0.3,         // Volume relativo da música
    "narration_volume": 1.0,     // Volume relativo da narração
    "sfx_timings": [             // Efeitos sonoros com timings
      { "time": 2.0, "effect": "door_open", "volume": 0.8 },
      { "time": 5.5, "effect": "footsteps", "volume": 0.6 }
    ]
  }
}
```

##### **3.2. Geração Durante Produção**
Modificar `/app/backend/routers/studio/production.py`:

```python
# Após Sora 2 gerar vídeo (linha 502-507)
if video_bytes and len(video_bytes) > 1000:
    # 1. Upload vídeo base (sem áudio)
    video_base_url = _upload_to_storage(video_bytes, f"studio/{project_id}_scene_{scene_num}_base.mp4", "video/mp4")
    
    # 2. Gerar narração (se cena tem diálogo)
    narration_url = None
    if scene.get("dialogue"):
        narration_url = await _generate_and_upload_narration(
            project_id, scene_num, scene["dialogue"], 
            voice_config, language
        )
    
    # 3. Gerar música (se projeto tem music plan)
    music_url = await _generate_scene_music(project_id, scene_num, scene.get("mood"))
    
    # 4. Mesclar tudo para criar "final_mix"
    final_video_url = await _merge_layers_to_final(
        video_base_url, narration_url, music_url, 
        timeline_config
    )
    
    # 5. Salvar TODAS as camadas
    _save_scene_with_layers(tenant_id, project_id, scene_num, {
        "video_base": video_base_url,
        "narration": narration_url,
        "music": music_url,
        "final_mix": final_video_url,
        "timeline": timeline_config
    })
```

##### **3.3. API de Exportação**
Novo endpoint: `/api/studio/projects/{project_id}/export-layers`

```python
@router.post("/projects/{project_id}/export-layers")
async def export_project_layers(project_id: str, format: str = "capcut"):
    """Export project with separate layers for external editing.
    
    Formats supported:
    - "capcut": CapCut project file (.ccut)
    - "premiere": Adobe Premiere project (.prproj)
    - "zip": Raw files (video + audio tracks) in ZIP
    """
    project = _get_project(tenant_id, project_id)
    
    if format == "zip":
        # Simple: ZIP all layer files
        return _export_as_zip(project)
    
    elif format == "capcut":
        # Generate CapCut project file
        return _export_to_capcut(project)
    
    elif format == "premiere":
        # Generate Premiere project XML
        return _export_to_premiere(project)
```

##### **3.4. UI de Exportação**
Adicionar botão no frontend (DirectedStudio.jsx):

```jsx
{/* Novo botão de exportação por camadas */}
<button onClick={handleExportLayers} className="flex items-center gap-2">
  <Download size={16} />
  <span>Exportar Camadas</span>
</button>

{/* Modal de escolha de formato */}
<ExportLayersModal
  isOpen={showExportModal}
  onClose={() => setShowExportModal(false)}
  onExport={(format) => {
    // "zip", "capcut", "premiere"
    downloadProjectLayers(projectId, format);
  }}
/>
```

##### **3.5. Compatibilidade com CapCut**
CapCut suporta importação de projetos via arquivo `.ccut` (JSON):

```json
{
  "version": "1.0",
  "tracks": [
    {
      "type": "video",
      "clips": [
        {
          "path": "scene_1_base.mp4",
          "start": 0,
          "duration": 12.3,
          "volume": 0
        }
      ]
    },
    {
      "type": "audio",
      "clips": [
        {
          "path": "scene_1_narration.mp3",
          "start": 0.5,
          "duration": 11.8,
          "volume": 100
        },
        {
          "path": "scene_1_music.mp3",
          "start": 0,
          "duration": 12.3,
          "volume": 30
        }
      ]
    }
  ]
}
```

---

### **FASE 4: Testes e Validação** 🧪
1. **Teste de Áudio**:
   - Regenerar narração em projeto existente
   - Verificar idioma 100% consistente
   - Verificar texto exato está sendo falado

2. **Teste de Editar/Regenerar**:
   - Clicar em "Editar" → Form deve abrir
   - Modificar diálogo → Salvar
   - Clicar em "Regenerar" → Vídeo deve regenerar

3. **Teste de Camadas**:
   - Exportar projeto com camadas
   - Importar em CapCut
   - Verificar que todas as faixas estão separadas

---

## 📊 **CRONOGRAMA**

### **Imediato (Hoje)**
1. ✅ Fase 1 completa (bugs de áudio)
2. 🔴 Debugar funções de Editar/Regenerar
3. 🔴 Corrigir problema (CSS, JavaScript, ou backend)

### **Próximo (Após aprovação)**
1. 🆕 Implementar sistema de camadas
2. 🆕 Criar API de exportação
3. 🆕 Adicionar UI de exportação

### **Futuro (Se necessário)**
1. Suporte para outros formatos (Premiere, DaVinci Resolve)
2. Editor de timeline integrado no StudioX
3. Pré-visualização de camadas separadas

---

## 🎬 **PRÓXIMOS PASSOS IMEDIATOS**

**AGORA (Prioridade 1):**
1. Debugar por que "Editar" e "Regenerar" não funcionam
2. Capturar screenshot/logs do erro
3. Corrigir problema

**DEPOIS (Prioridade 2):**
1. Usuário testa correções de áudio (Fase 1)
2. Se aprovado, implementar sistema de camadas (Fase 3)

---

## 📝 **PERGUNTAS PENDENTES**

1. **Sistema de Camadas**:
   - Você quer exportação em formato CapCut (.ccut)?
   - Ou prefere ZIP simples com arquivos separados?
   - Precisa de outros formatos (Premiere, DaVinci)?

2. **Prioridade**:
   - Devo focar PRIMEIRO em corrigir Editar/Regenerar?
   - Ou você prefere que eu implemente camadas primeiro?

---

**Status Atual**: 
- ✅ Fase 1 (Áudio) completa
- 🔴 Fase 2 (UI) em investigação
- ⏳ Fase 3 (Camadas) aguardando aprovação
