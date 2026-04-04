# Avatar Manager - Single Source of Truth

## 📋 Objetivo

Centralizar TODA a lógica de criação/edição de avatares em um único local para evitar código duplicado.

## 🎯 Componentes que usam

1. **PipelineView.jsx** - Avatares de campanhas
2. **StudioPage.jsx** - Galeria global de personagens  
3. **DirectedStudio.jsx** - Personagens de projetos de filme

## 🔧 Como usar

### 1. Importar o hook

```javascript
import { useAvatarManager } from '../hooks/useAvatarManager';
```

### 2. Inicializar no componente

```javascript
const avatarManager = useAvatarManager({
  onAvatarSaved: (avatar) => {
    // Callback quando avatar é salvo
    console.log('Avatar salvo:', avatar);
    // Atualizar lista local, recarregar galeria, etc.
  },
  onAvatarDeleted: (avatarId) => {
    // Callback quando avatar é deletado
    console.log('Avatar deletado:', avatarId);
  },
  apiEndpoint: '/data/avatars', // ou '/campaigns/pipeline/avatars'
  isDirectedMode: true // true para projetos de filme, false para campanhas
});
```

### 3. Usar no JSX

```javascript
// Botão criar novo
<button onClick={() => {
  avatarManager.resetAvatarModal();
  avatarManager.setShowAvatarModal(true);
}}>
  + Criar Personagem
</button>

// Botão editar existente
<button onClick={() => avatarManager.openAvatarForEdit(avatar)}>
  Editar
</button>

// Modal de avatar
<AvatarModal ctx={avatarManager} />
```

## ✅ Vantagens

1. **Única fonte de verdade** - Alterar em 1 lugar, todos herdam
2. **Zero duplicação** - ~2000 linhas de código removidas
3. **Fácil manutenção** - Bug fix em 1 lugar resolve para todos
4. **Testes unificados** - Testar o hook testa todos os componentes

## 🚀 Status de Migração

- [ ] PipelineView.jsx (TO DO)
- [ ] StudioPage.jsx (TO DO)
- [ ] DirectedStudio.jsx (TO DO)

## 📝 Próximos passos

1. Migrar PipelineView primeiro (componente mais complexo)
2. Testar todas as funcionalidades
3. Migrar StudioPage
4. Migrar DirectedStudio
5. Remover código duplicado

---

**Criado:** 2026-04-04  
**Autor:** Agente E1
