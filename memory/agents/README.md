# StudioX AI Agents Registry

## 📋 Sistema de Agentes Especializados

Este diretório contém a especificação completa de todos os agentes de IA que trabalham no StudioX.

## 🎯 Estrutura

Cada agente tem um arquivo JSON com:
- Nome e descrição
- Responsabilidades
- Prompt system
- Input/Output esperados
- Quality criteria
- Exemplos

## 🤖 Agentes Ativos

### **FASE 1: Pesquisa (Research Phase)**
1. `researcher_agent.json` - Pesquisador de Fatos Históricos
2. `narrative_researcher_agent.json` - Pesquisador de Estruturas Narrativas
3. `visual_researcher_agent.json` - Pesquisador de Referências Visuais
4. `production_analyst_agent.json` - Analista de Produção

### **FASE 2: Consenso (Consensus Room)**
5. `orchestrator_agent.json` - Orquestrador da Sala de Reunião
6. `conflict_resolver_agent.json` - Resolvedor de Conflitos entre Agentes

### **FASE 3: Produção (Production Phase)**
7. `screenwriter_agent.json` - Roteirista (Estrutura Narrativa)
8. `dialogue_writer_agent.json` - Escritor de Diálogos Cinematográficos
9. `narrator_agent.json` - Escritor de Narração
10. `visual_director_agent.json` - Diretor Visual (Storyboard)
11. `sound_designer_agent.json` - Designer de Som e Vozes

### **FASE 4: Validação (Quality Assurance)**
12. `quality_validator_agent.json` - Validador de Qualidade
13. `consistency_checker_agent.json` - Verificador de Consistência

### **FASE 5: Execução (Production)**
14. `video_producer_agent.json` - Produtor de Vídeos (Sora 2)
15. `audio_producer_agent.json` - Produtor de Áudio

## 📊 Uso

Os agentes são carregados dinamicamente pelo sistema e podem ser:
- Visualizados na página `/agents`
- Editados para ajuste fino
- Versionados para rollback
