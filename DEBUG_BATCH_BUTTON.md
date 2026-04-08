# 🐛 DEBUG: Botão "Em Lote" Não Ativa

## Como Testar Manualmente

### Passo 1: Abrir Console do Navegador
1. Pressione `F12` ou `Cmd+Option+I` (Mac)
2. Vá para a aba "Console"
3. **Deixe o console aberto** durante todo o teste

### Passo 2: Abrir Modal de Criar Personagem
1. Entre no Studio X
2. Procure o botão "Criar Personagem" ou "Novo Personagem"
3. Clique nele

### Passo 3: Selecionar "Por Prompt"
1. No modal que abrir, clique em **"Por Prompt"**
2. Você deve ver dois botões aparecerem: **"Individual"** e **"Em Lote"**

### Passo 4: Tentar Clicar em "Em Lote"
1. Clique no botão **"Em Lote"**
2. **OBSERVE O CONSOLE** - deve aparecer:
   ```
   🔘 Em Lote button clicked
   setPromptBatchMode exists? true
   📊 promptBatchMode changed: true
   ```

### Passo 5: Verificar Mudanças na UI
Quando clicar em "Em Lote", deve acontecer:

✅ **O que DEVE mudar:**
- Botão "Em Lote" fica roxo/destaca (borda roxa)
- Botão "Individual" fica cinza
- Título muda para: "Cole os prompts completos (separe com linha em branco)"
- Textarea fica maior (altura aumenta)
- Placeholder muda para mostrar exemplo de prompts separados
- Aparece aviso azul: "💡 Como usar: Cole seus prompts..."
- Contador mostra: "0 personagens serão criados" (ou número baseado no texto)

❌ **Se NÃO mudar:**
- Botão não responde ao clique
- UI permanece igual
- Nada aparece no console

---

## O Que Verificar no Console

### Console Logs Esperados:

**Ao clicar "Em Lote":**
```
🔘 Em Lote button clicked
setPromptBatchMode exists? true
📊 promptBatchMode changed: true
```

**Ao clicar "Individual":**
```
🔘 Individual button clicked
📊 promptBatchMode changed: false
```

### Se NÃO aparecer nada no console:
Significa que o `onClick` não está sendo chamado. Possíveis causas:
- Outro elemento está bloqueando o clique
- Modal não está renderizando corretamente
- Context não está sendo passado

### Se aparecer só "🔘 Em Lote button clicked":
Significa que o `setPromptBatchMode` não existe no context.

---

## Troubleshooting

### Problema 1: Console está vazio
**Solução:** Recarregue a página (Ctrl+R ou Cmd+R)

### Problema 2: "setPromptBatchMode exists? false"
**Causa:** Context não está sendo passado corretamente
**Solução:** Preciso verificar o código de passagem do context

### Problema 3: Botão não responde visualmente
**Causa:** CSS não está aplicando ou state não está mudando
**Solução:** Verificar se o `promptBatchMode` está chegando no componente

### Problema 4: Erro no console
**Solução:** Me envie o erro completo

---

## O Que Me Enviar

Por favor, me envie:

1. **Screenshot do modal aberto** (antes de clicar em "Em Lote")
2. **Screenshot após clicar em "Em Lote"** (para ver se mudou algo)
3. **Todo o conteúdo do console** (copie e cole o texto)
4. **Confirme:** Você vê os dois botões "Individual" e "Em Lote"?

---

## Alternativa: Teste Rápido

Se preferir, posso criar um botão de teste temporário que força o modo batch, para verificar se o problema é no toggle ou em outra parte do código.
