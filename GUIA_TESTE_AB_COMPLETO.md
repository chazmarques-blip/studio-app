# 🎬 GUIA COMPLETO: TESTE A/B SORA vs KLING

## 🎯 OBJETIVO
Criar **2 projetos idênticos** com as mesmas 3 cenas, mas gerando vídeos com engines diferentes:
- **Projeto A:** Sora 2 (OpenAI)
- **Projeto B:** Kling AI (Kuaishou)

Depois comparar lado a lado para decidir qual é melhor.

---

## 📋 PASSO A PASSO

### **PASSO 1: CRIAR PROJETO A (SORA 2)**

**1.1. No StudioX, clique em "Criar Projecto"**

**1.2. Preencha os dados:**
```
Nome: Teste Sora - Encontro dos Amigos
Idioma: Português
Estilo Visual: Animation → Pixar 3D
```

**1.3. Cole o briefing:**
```
Uma história curta e doce sobre três amigos inseparáveis: Abraão Baby e Sara Baby (dois camelos bebês antropomórficos) e a Estrela Guia (uma estrela mágica falante). Eles vivem aventuras no deserto, brincam juntos e celebram sua amizade eterna. Estilo Pixar 3D, cores vibrantes, atmosfera alegre e emocionante.
```

**1.4. Criar projeto e aguardar**
- Sistema vai gerar roteiro automaticamente
- Esperar até aparecer as cenas

**1.5. IMPORTANTE: Sincronizar Biblizoo Baby**
- Ir em "Personagens"
- Clicar "Sincronizar com Biblioteca"
- Escolher pasta **"Biblizoo Baby"**
- Garantir que Abraão Baby e Sara Baby foram puxados

**1.6. Editar cenas manualmente (CRÍTICO PARA TESTE)**

Vá em cada cena e **substitua** o conteúdo pelo script de teste:

**CENA 1:**
```
Título: O Amanhecer no Deserto
Descrição: Amanhecer no deserto com dunas douradas. Abraão Baby e Sara Baby estão sentados lado a lado sobre um tapete colorido, observando o sol nascente no horizonte. Raios dourados iluminam suas faces peludas. Eles conversam animados.
Diálogo: 
Abraão Baby: "Que dia lindo, Sara! O sol nasceu só para nós!"
Sara Baby: "E olha quem vem brilhando lá no céu, Abraão!"
Estrela Guia: "Bom dia, amiguinhos! Prontos para uma aventura?"
Emoção: esperançoso
Câmera: Wide shot → Close-up nos rostos → Pan up para o céu
Personagens: Abraão Baby, Sara Baby, Estrela Guia
```

**CENA 2:**
```
Título: Brincando Entre as Dunas
Descrição: Abraão Baby e Sara Baby correm e pulam entre dunas de areia dourada. A Estrela Guia flutua ao lado deles, deixando um rastro de brilho dourado. Borboletas amarelas voam ao redor. Risos infantis enchem o ar.
Diálogo:
Sara Baby: "Não consigo te pegar, Estrela Guia!"
Estrela Guia: "Sou rápida como a luz! Hihihi!"
Abraão Baby: "Espera por nós! Queremos brincar também!"
Emoção: brincalhão
Câmera: Tracking shot seguindo movimento → Low angle nas dunas → Wide shot do grupo
Personagens: Abraão Baby, Sara Baby, Estrela Guia
```

**CENA 3:**
```
Título: O Abraço da Amizade
Descrição: Final de tarde com céu laranja e roxo. Os três amigos se reúnem em círculo. Abraão Baby e Sara Baby abrem os braços e abraçam a Estrela Guia (que brilha intensamente no centro). Partículas douradas flutuam ao redor formando corações luminosos.
Diálogo:
Abraão Baby: "Vocês são os melhores amigos do mundo!"
Sara Baby: "Juntos somos mais fortes e felizes!"
Estrela Guia: "Brilharei para sempre ao lado de vocês!"
Emoção: ternura
Câmera: Medium shot → Slow dolly in → Close-up no abraço com bokeh mágico
Personagens: Abraão Baby, Sara Baby, Estrela Guia
```

**1.7. MANTER Sora 2 como engine (já é padrão)**
- Não precisa fazer nada
- Projeto usa Sora automaticamente

**1.8. Ir para PRODUÇÃO**
- Clicar "Iniciar Produção"
- Aguardar geração (Sora demora ~5-10min para 3 cenas)
- **Anotar tempo de início e fim**

---

### **PASSO 2: CRIAR PROJETO B (KLING AI)**

**2.1. DUPLICAR ou criar novo projeto**

**Opção A - Criar do zero (mais seguro):**
- Clicar "Criar Projecto" novamente
- Nome: **"Teste Kling - Encontro dos Amigos"**
- **REPETIR EXATAMENTE os passos 1.2 a 1.6** (mesmo briefing, mesmas cenas)

**Opção B - Console do navegador (mais rápido mas técnico):**

Se você já criou Projeto A, pode criar uma cópia via API:

```javascript
// 1. Pegar dados do Projeto A
const projectA_ID = "SEU_PROJECT_ID_AQUI"; // Copie da URL do projeto

fetch(`${window.location.origin}/api/studio/projects/${projectA_ID}`)
  .then(r => r.json())
  .then(projectA => {
    // 2. Criar Projeto B como cópia
    const projectB = {
      name: "Teste Kling - Encontro dos Amigos",
      briefing: projectA.briefing,
      language: projectA.language,
      visual_style: projectA.visual_style,
      animation_sub: projectA.animation_sub,
      scenes: projectA.scenes, // Mesmas cenas!
      characters: projectA.characters, // Mesmos personagens!
      character_avatars: projectA.character_avatars,
      video_engine: "kling"  // <-- DIFERENÇA CRÍTICA!
    };
    
    // 3. Criar via API
    return fetch(`${window.location.origin}/api/studio/projects`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify(projectB)
    });
  })
  .then(r => r.json())
  .then(newProject => {
    console.log('✅ Projeto B criado com KLING:', newProject);
    console.log('ID:', newProject.id);
    console.log('Abra:', `${window.location.origin}/studio/projects/${newProject.id}`);
  })
  .catch(e => console.error('❌ Erro:', e));
```

**2.2. TROCAR ENGINE para Kling (SE criou do zero)**

Se criou Projeto B manualmente, precisa trocar engine via console:

```javascript
const projectB_ID = "SEU_PROJECT_B_ID"; // Copie da URL

fetch(`${window.location.origin}/api/studio/projects/${projectB_ID}`, {
  method: 'PATCH',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  },
  body: JSON.stringify({ video_engine: "kling" })
})
.then(r => r.json())
.then(d => console.log('✅ Projeto B agora usa KLING:', d));
```

**2.3. Verificar que está usando Kling:**

```javascript
fetch(`${window.location.origin}/api/studio/projects/${projectB_ID}`)
  .then(r => r.json())
  .then(p => {
    console.log('Engine:', p.video_engine || 'sora');
    if (p.video_engine === 'kling') {
      console.log('✅ KLING CONFIRMADO!');
    } else {
      console.error('❌ AINDA É SORA! Rode o PATCH novamente.');
    }
  });
```

**2.4. Ir para PRODUÇÃO**
- Clicar "Iniciar Produção" no Projeto B
- Aguardar geração (Kling pode demorar ~8-15min para 3 cenas)
- **Anotar tempo de início e fim**

---

## 📊 PASSO 3: COMPARAR RESULTADOS

### **3.1. Ver vídeos lado a lado**

Abra ambos projetos em abas diferentes:
- Aba 1: Projeto A (Sora)
- Aba 2: Projeto B (Kling)

Vá para "Resultados" em ambos.

### **3.2. Preencher checklist de comparação**

Use este template:

```markdown
# COMPARAÇÃO: SORA 2 vs KLING AI

## ⏱️ TEMPO DE GERAÇÃO
- Sora 2: ____ minutos
- Kling AI: ____ minutos
- 🏆 Vencedor: ______

## 🎨 CONTINUIDADE VISUAL

### Cena 1 → Cena 2
- Sora: Abraão Baby manteve cor laranja? [SIM/NÃO]
- Kling: Abraão Baby manteve cor laranja? [SIM/NÃO]
- Sora: Sara Baby manteve bochechas rosa? [SIM/NÃO]
- Kling: Sara Baby manteve bochechas rosa? [SIM/NÃO]
- 🏆 Vencedor: ______

### Cena 2 → Cena 3
- Sora: Personagens consistentes? [SIM/NÃO]
- Kling: Personagens consistentes? [SIM/NÃO]
- 🏆 Vencedor: ______

## 🗣️ LIP SYNC

### Cena 1
- Sora: Boca sincronizada com diálogo? [1-5 ⭐]
- Kling: Boca sincronizada com diálogo? [1-5 ⭐]
- 🏆 Vencedor: ______

### Cena 2
- Sora: Expressões naturais? [1-5 ⭐]
- Kling: Expressões naturais? [1-5 ⭐]
- 🏆 Vencedor: ______

### Cena 3
- Sora: Gestos combinam com fala? [1-5 ⭐]
- Kling: Gestos combinam com fala? [1-5 ⭐]
- 🏆 Vencedor: ______

## 🇧🇷 TEXTOS EM PORTUGUÊS
- Sora: Algum texto em inglês apareceu? [SIM/NÃO]
- Kling: Algum texto em inglês apareceu? [SIM/NÃO]
- 🏆 Vencedor: ______

## 🎬 QUALIDADE GERAL

### Cena 1
- Sora: Qualidade geral [1-5 ⭐]
- Kling: Qualidade geral [1-5 ⭐]
- 🏆 Vencedor: ______

### Cena 2
- Sora: Movimentos fluidos [1-5 ⭐]
- Kling: Movimentos fluidos [1-5 ⭐]
- 🏆 Vencedor: ______

### Cena 3
- Sora: Iluminação e cores [1-5 ⭐]
- Kling: Iluminação e cores [1-5 ⭐]
- 🏆 Vencedor: ______

## 💰 CUSTO ESTIMADO
- Sora 2: ~$0.36 (3 cenas x $0.12)
- Kling AI: ~$0.15 (3 cenas x $0.05)
- 🏆 Vencedor: KLING (60% mais barato)

## 🏆 RESULTADO FINAL
- Continuidade: [SORA/KLING/EMPATE]
- Lip Sync: [SORA/KLING/EMPATE]
- Textos PT: [SORA/KLING/EMPATE]
- Qualidade: [SORA/KLING/EMPATE]
- Custo: KLING
- Velocidade: [SORA/KLING/EMPATE]

### DECISÃO:
[X] Continuar com SORA 2
[X] Migrar para KLING AI
[X] Usar AMBOS (conforme necessidade)

### OBSERVAÇÕES:
_____________________________
_____________________________
_____________________________
```

---

## 🎥 PASSO 4: EXPORTAR VÍDEOS PARA COMPARAÇÃO

### **4.1. Download dos vídeos**

Para cada projeto, vá em "Resultados" e baixe:
- Vídeo completo concatenado (se disponível)
- OU vídeos individuais das 3 cenas

### **4.2. Criar vídeo comparativo lado a lado (opcional)**

Se quiser criar um vídeo mostrando Sora | Kling lado a lado:

```bash
# Usando FFmpeg (se tiver acesso ao terminal)
ffmpeg -i sora_cena1.mp4 -i kling_cena1.mp4 \
  -filter_complex "[0:v]scale=640:360,pad=1280:360:0:0[left]; \
                   [1:v]scale=640:360[right]; \
                   [left][right]overlay=640:0" \
  -c:v libx264 -crf 20 \
  comparacao_cena1.mp4
```

---

## ⚡ RESUMO RÁPIDO (TL;DR)

```
1. Criar "Projeto A - Sora" com 3 cenas do script
2. Produzir com Sora 2 (padrão)
3. Criar "Projeto B - Kling" com MESMAS 3 cenas
4. Trocar engine: project.video_engine = "kling"
5. Produzir com Kling AI
6. Comparar lado a lado
7. Decidir qual é melhor!
```

---

## 🆘 AJUDA RÁPIDA

### **Como saber qual engine um projeto está usando?**
```javascript
// Console do navegador
fetch(`${window.location.origin}/api/studio/projects/SEU_ID`)
  .then(r => r.json())
  .then(p => console.log('Engine:', p.video_engine || 'sora (padrão)'));
```

### **Kling não está gerando?**
```bash
# Ver logs
tail -f /var/log/supervisor/backend.out.log | grep -i "kling"
```

### **Quero cancelar geração e tentar de novo?**
- Atualmente não há botão "Cancelar" no UI
- Pode fechar aba e aguardar timeout (~10min)
- Ou restart backend (perde progresso)

---

**Boa sorte com o teste! 🚀**
**Me avise os resultados da comparação!**
