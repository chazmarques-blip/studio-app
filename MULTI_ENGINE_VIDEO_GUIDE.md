# 🎬 StudioX - Suporte Multi-Engine de Vídeo

## ✅ FIXES CRÍTICOS APLICADOS (2026-04-07)

### **FIX #1: Aumento do Limite de Prompt**
- **Antes:** 1000 caracteres (truncava character_bible e language_marker)
- **Depois:** 2500 caracteres (prompts completos)
- **Arquivo:** `/app/backend/routers/studio/production.py` linha ~580

### **FIX #2: Language Marker no Início**
- **Antes:** `"Any visible text in PORTUGUESE TEXT"` no FINAL do prompt (era truncado)
- **Depois:** `"[CRITICAL: All visible text must be in PORTUGUESE TEXT]"` logo APÓS style_anchors
- **Resultado:** Language enforcement não será mais perdido por truncamento

### **FIX #3: Reference Image Enforcement**
- Adicionado: `"MATCH THE CHARACTER REFERENCE IMAGE EXACTLY FOR ALL CHARACTERS"` no system prompt
- Reforça que o composite avatar deve ser respeitado

---

## 🚀 NOVO: SUPORTE MULTI-ENGINE

O StudioX agora suporta **2 engines de geração de vídeo**:

| Engine | Duração | Continuidade | Lip Sync | Custo | Status |
|--------|---------|--------------|----------|-------|--------|
| **Sora 2** | 12s | ⭐⭐⭐⭐ | ⭐⭐⭐ | $$$$ | ✅ Padrão |
| **Kling AI** | 5min | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $$ | ✅ Disponível |

---

## 🎯 COMO USAR

### **Opção A: Sora 2 (Padrão)**

Não precisa fazer nada. Sora 2 é o engine padrão.

```python
# Projeto usa Sora 2 automaticamente
project = {
    "title": "Minha História",
    # ... resto do projeto
}
```

### **Opção B: Kling AI**

Adicione `"video_engine": "kling"` ao projeto:

```python
project = {
    "title": "Minha História",
    "video_engine": "kling",  # <-- Usa Kling AI
    # ... resto do projeto
}
```

**Via API:**
```bash
curl -X PATCH $API/studio/projects/{project_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"video_engine": "kling"}'
```

**Credentials necessárias:**
Adicionar ao `.env` do backend:
```bash
KLING_ACCESS_KEY=your_access_key_here
KLING_SECRET_KEY=your_secret_key_here
```

---

## 📊 COMPARAÇÃO DETALHADA

### **Sora 2 (OpenAI)**

**Vantagens:**
- ✅ Qualidade visual consistente
- ✅ API bem documentada e estável
- ✅ Suporte técnico OpenAI
- ✅ Já integrado e testado

**Desvantagens:**
- ❌ Vídeos curtos (12s) - precisa dividir história
- ❌ Prompts truncados em 1000 chars (AGORA FIXADO: 2500)
- ❌ Lip sync básico
- ❌ Textos em português ignorados às vezes
- ❌ Caro (~$0.12/segundo)

### **Kling AI (Kuaishou)**

**Vantagens:**
- ✅ Vídeos até **5 MINUTOS** (sem divisão!)
- ✅ Character reference mode (continuidade superior)
- ✅ Lip sync melhor que Sora
- ✅ Suporta prompts até 2500 chars nativamente
- ✅ 60% mais barato (~$0.05/segundo)

**Desvantagens:**
- ⚠️ API em beta (pode ter bugs)
- ⚠️ Documentação limitada
- ⚠️ Servidor na China (latência maior)
- ⚠️ Menos testado em produção
- ⚠️ Suporte técnico em inglês/chinês

---

## 🧪 TESTE A/B RECOMENDADO

**1. Criar 2 projetos idênticos:**
```python
project_sora = {
    "title": "Teste Abraão - Sora",
    "video_engine": "sora",  # ou omitir (é padrão)
    # ... mesmo briefing, personagens, cenas
}

project_kling = {
    "title": "Teste Abraão - Kling",
    "video_engine": "kling",
    # ... mesmo briefing, personagens, cenas
}
```

**2. Gerar 3-5 cenas de cada**

**3. Comparar:**
- [ ] Continuidade visual (Abraão tem mesma aparência?)
- [ ] Lip sync (boca sincronizada com áudio?)
- [ ] Textos em português (aparecem corretamente?)
- [ ] Tempo de geração
- [ ] Custo total
- [ ] Qualidade geral

**4. Decidir qual usar em produção**

---

## 💰 ESTIMATIVA DE CUSTOS

Para um projeto de **25 cenas x 12s = 300s (5 minutos)**:

| Engine | Custo Estimado | Tempo de Geração | Qualidade Lip Sync |
|--------|----------------|------------------|-------------------|
| **Sora 2** | ~$150 | ~45min (25 jobs) | ⭐⭐⭐ |
| **Kling AI** | ~$60 | ~30min (1 job longo) | ⭐⭐⭐⭐ |

**Economia com Kling:** ~$90 (60%) + 15min mais rápido

---

## 🔧 TROUBLESHOOTING

### **Kling AI não funciona**

**Erro:** `Kling AI credentials not found`

**Solução:**
```bash
# Backend .env
KLING_ACCESS_KEY=ak-xxxxxxxxxx
KLING_SECRET_KEY=sk-xxxxxxxxxx

# Restart backend
sudo supervisorctl restart backend
```

### **Kling retorna vídeo vazio**

**Possíveis causas:**
1. Credentials inválidas
2. API rate limit excedido
3. Prompt contém conteúdo proibido
4. Timeout (vídeo longo demora)

**Debug:**
```bash
# Ver logs do backend
tail -f /var/log/supervisor/backend.out.log | grep -i "kling"
```

### **Sora 2 ainda trunca prompts**

**Verificar:** O fix foi aplicado?
```bash
grep "prompt=sora_prompt\[:2500\]" /app/backend/routers/studio/production.py
```

Deve retornar a linha com `[:2500]`. Se retornar `[:1000]`, o fix não foi aplicado.

---

## 📝 LOGS E DEBUG

**Ver qual engine está sendo usado:**
```bash
tail -f /var/log/supervisor/backend.out.log | grep "Using.*engine"
```

**Output esperado:**
```
Studio [abc123]: Using SORA 2 engine (OpenAI SDK)
# OU
Studio [abc123]: Using KLING AI engine (v3)
```

**Ver prompts completos sendo enviados:**
```bash
grep "FINAL Sora prompt" /var/log/supervisor/backend.out.log | tail -1
```

---

## 🎯 PRÓXIMOS PASSOS

### **Curto Prazo (Agora)**
- [x] Aplicar fixes críticos no Sora 2
- [x] Integrar Kling AI como opção
- [ ] Testar ambos engines com projeto "Abraao e Isaac"
- [ ] Comparar resultados

### **Médio Prazo (1-2 semanas)**
- [ ] Decidir engine padrão baseado em testes
- [ ] Otimizar prompts para engine escolhido
- [ ] Implementar fallback automático (Kling → Sora se falhar)

### **Longo Prazo (1+ mês)**
- [ ] Pipeline híbrido (Kling + Wav2Lip para lip sync perfeito)
- [ ] Suporte para Runway Gen-3 (terceiro engine)
- [ ] Cache de vídeos gerados para regeneração rápida

---

## 📚 REFERÊNCIAS

- **Kling AI Docs:** https://kling.ai/document-api/quickStart/userManual
- **Sora 2 Docs:** https://platform.openai.com/docs/guides/video
- **Código:** `/app/backend/core/kling_client.py`

---

**Última atualização:** 2026-04-07
**Versão:** v4.1 (Multi-Engine Support)
