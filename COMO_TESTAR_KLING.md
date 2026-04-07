# 🎬 GUIA RÁPIDO: TESTAR KLING AI NO STUDIOX

## ✅ CREDENCIAIS CONFIGURADAS

As credenciais do Kling AI já foram adicionadas ao backend:
- Access Key: `AaeDp...` ✅
- Secret Key: `nPCCD...` ✅
- Status: **ATIVO E PRONTO**

---

## 🚀 COMO TESTAR

### **MÉTODO 1: Via Console do Navegador (Mais Rápido)**

1. **Abra o projeto "Abraao e Isaac baby" existente**

2. **Abra o Console do navegador** (F12 → Console)

3. **Execute este comando:**
```javascript
// Pegar o project_id atual
const projectId = "4e91eaf83c51";  // Seu projeto atual

// Fazer PATCH para trocar engine para Kling
fetch(`${window.location.origin}/api/studio/projects/${projectId}`, {
  method: 'PATCH',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  },
  body: JSON.stringify({
    video_engine: "kling"  // <-- USA KLING!
  })
})
.then(r => r.json())
.then(d => console.log('✅ Engine trocado para KLING:', d))
.catch(e => console.error('❌ Erro:', e));
```

4. **Regenerar uma cena de teste** (ex: cena 2, 4, 5...)
   - Clique no botão "Gerar Vídeo" de uma cena não criada

5. **Verificar logs do backend:**
```bash
# No terminal do servidor
tail -f /var/log/supervisor/backend.out.log | grep -i "kling\|engine"
```

**Output esperado:**
```
Studio [abc123]: Using KLING AI engine (v3)
🎬 Using KLING AI engine (duration=12s)
Kling AI: Submitting T2V request (dur=12.0s, model=kling-v3)
Kling AI: Task xyz123 submitted, polling for completion...
Kling AI: Task xyz123 still processing... (15s elapsed)
Kling AI: Task xyz123 DONE in 45s (2048KB)
```

---

### **MÉTODO 2: Criar Novo Projeto de Teste**

**Atualmente, o frontend NÃO tem UI para escolher engine.**

**Opções:**

**A) Via API diretamente:**
```bash
curl -X POST $API/studio/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Teste Kling - Abraão",
    "briefing": "História de Abraão e Isaac com personagens 3D",
    "language": "pt",
    "video_engine": "kling",
    "visual_style": "animation"
  }'
```

**B) Modificar projeto existente (console do navegador):**
```javascript
// Após criar projeto normalmente no StudioX
const projectId = "SEU_PROJECT_ID";  // Copie da URL

fetch(`${window.location.origin}/api/studio/projects/${projectId}`, {
  method: 'PATCH',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  },
  body: JSON.stringify({ video_engine: "kling" })
})
.then(r => r.json())
.then(d => console.log('✅ Trocado para Kling:', d));
```

---

## 📊 COMPARAR SORA vs KLING

### **Teste A/B Sugerido:**

**1. Pegar 3 cenas do projeto atual:**
   - Cena 2: "Olhando as Estrelas"
   - Cena 4: "A Visita do Anjo Gabriel"  
   - Cena 9: "Brincando no Deserto"

**2. Gerar com Sora 2 (já feito):**
   - Projeto atual usa Sora por padrão
   - Vídeos já gerados

**3. Gerar as MESMAS 3 cenas com Kling:**
```javascript
// No console, trocar para Kling
const projectId = "4e91eaf83c51";
fetch(`${window.location.origin}/api/studio/projects/${projectId}`, {
  method: 'PATCH',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  },
  body: JSON.stringify({ video_engine: "kling" })
})
.then(() => {
  console.log('✅ Trocado para Kling!');
  console.log('Agora clique "Gerar Vídeo" nas cenas 2, 4, 9');
});
```

**4. Comparar:**
- [ ] **Continuidade:** Abraão e Sara mantêm mesma aparência?
- [ ] **Lip sync:** Boca sincronizada com áudio?
- [ ] **Textos:** Aparecem em português?
- [ ] **Tempo:** Quanto tempo levou cada engine?
- [ ] **Qualidade:** Qual ficou melhor?
- [ ] **Custo:** Kling é 60% mais barato?

---

## 🔍 VERIFICAR QUAL ENGINE ESTÁ ATIVO

### **Via Console do Navegador:**
```javascript
fetch(`${window.location.origin}/api/studio/projects/4e91eaf83c51`)
  .then(r => r.json())
  .then(d => {
    const engine = d.video_engine || 'sora';
    console.log('🎬 Engine atual:', engine.toUpperCase());
    console.log(engine === 'kling' ? '✅ KLING ATIVO' : '✅ SORA ATIVO (padrão)');
  });
```

### **Via Logs do Backend:**
```bash
tail -f /var/log/supervisor/backend.out.log | grep -i "using.*engine"
```

---

## 🎯 VOLTARALIZAR PARA SORA

Se quiser voltar para Sora 2:

```javascript
const projectId = "4e91eaf83c51";
fetch(`${window.location.origin}/api/studio/projects/${projectId}`, {
  method: 'PATCH',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  },
  body: JSON.stringify({ video_engine: "sora" })
})
.then(r => r.json())
.then(d => console.log('✅ Voltou para SORA 2:', d));
```

---

## ⚠️ TROUBLESHOOTING

### **Kling não gera vídeo:**

**1. Verificar credenciais:**
```bash
grep "KLING" /app/backend/.env
```

Deve mostrar:
```
KLING_ACCESS_KEY=AaeDpKpGkQbhe3mnMtfK3pky93BJC4Ph
KLING_SECRET_KEY=nPCCDNd8nCfnMeJGAdeNGg8F3GApPLLC
```

**2. Ver logs de erro:**
```bash
tail -n 100 /var/log/supervisor/backend.err.log | grep -i "kling"
```

**3. Testar autenticação:**
```bash
cd /app/backend
python3 -c "
from core.kling_client import KlingClient
client = KlingClient()
try:
    token = client._get_auth_token()
    print('✅ Auth OK:', token[:20] + '...')
except Exception as e:
    print('❌ Auth failed:', e)
"
```

---

## 📝 PRÓXIMOS PASSOS

**Curto Prazo (AGORA):**
1. ✅ Credenciais configuradas
2. ⏳ **Testar 2-3 cenas com Kling** (você precisa fazer)
3. ⏳ **Comparar com Sora** (lado a lado)

**Médio Prazo (Esta semana):**
4. ⏳ Decidir qual engine usar como padrão
5. ⏳ Adicionar UI no frontend para escolher engine
6. ⏳ Implementar fallback (Kling → Sora se falhar)

**Longo Prazo (Próximo mês):**
7. ⏳ Pipeline híbrido (Kling + Wav2Lip)
8. ⏳ Testar vídeos longos (5min) com Kling
9. ⏳ Otimizar custos

---

**Última atualização:** 2026-04-07 21:30
**Status:** ✅ PRONTO PARA TESTAR
