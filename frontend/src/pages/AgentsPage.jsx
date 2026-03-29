import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { ArrowLeft, Bot, Eye, Edit, Save, X, ChevronDown, ChevronUp } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const PHASE_COLORS = {
  research: 'bg-green-100 text-green-800',
  consensus: 'bg-blue-100 text-blue-800',
  production: 'bg-purple-100 text-purple-800',
  validation: 'bg-yellow-100 text-yellow-800',
  execution: 'bg-red-100 text-red-800',
};

const PHASE_LABELS = {
  research: 'Pesquisa',
  consensus: 'Consenso',
  production: 'Produção',
  validation: 'Validação',
  execution: 'Execução',
};

export function AgentsPage() {
  const navigate = useNavigate();
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [viewingAgent, setViewingAgent] = useState(null);
  const [editingAgent, setEditingAgent] = useState(null);
  const [expandedCards, setExpandedCards] = useState({});

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      const { data } = await axios.get(`${API}/studio/agents/registry`);
      setAgents(data.agents || []);
    } catch (error) {
      toast.error('Erro ao carregar agentes');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const viewAgent = async (agentId) => {
    try {
      const { data } = await axios.get(`${API}/studio/agents/registry/${agentId}`);
      setViewingAgent(data.agent);
    } catch (error) {
      toast.error('Erro ao carregar especificação do agente');
    }
  };

  const editAgent = (agent) => {
    setEditingAgent({ ...agent });
  };

  const saveAgent = async () => {
    try {
      await axios.put(`${API}/studio/agents/registry/${editingAgent.id}`, editingAgent);
      toast.success('Agente atualizado com sucesso!');
      setEditingAgent(null);
      loadAgents();
    } catch (error) {
      toast.error('Erro ao atualizar agente');
    }
  };

  const toggleExpand = (agentId) => {
    setExpandedCards(prev => ({
      ...prev,
      [agentId]: !prev[agentId]
    }));
  };

  // Group agents by phase
  const agentsByPhase = agents.reduce((acc, agent) => {
    const phase = agent.phase || 'other';
    if (!acc[phase]) acc[phase] = [];
    acc[phase].push(agent);
    return acc;
  }, {});

  const phaseOrder = ['research', 'consensus', 'production', 'validation', 'execution'];

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-slate-600">Carregando agentes...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/studio')}
            className="flex items-center gap-2 text-slate-600 hover:text-slate-900 mb-4"
          >
            <ArrowLeft size={20} />
            <span>Voltar</span>
          </button>
          <div className="flex items-center gap-4">
            <Bot size={40} className="text-violet-600" />
            <div>
              <h1 className="text-3xl font-bold text-slate-900">
                Agentes de IA do StudioX
              </h1>
              <p className="text-slate-600 mt-1">
                {agents.length} agentes especializados trabalhando em conjunto
              </p>
            </div>
          </div>
        </div>

        {/* Agents by Phase */}
        {phaseOrder.map(phase => {
          const phaseAgents = agentsByPhase[phase] || [];
          if (phaseAgents.length === 0) return null;

          return (
            <div key={phase} className="mb-8">
              <div className="flex items-center gap-3 mb-4">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${PHASE_COLORS[phase]}`}>
                  {PHASE_LABELS[phase]}
                </span>
                <span className="text-slate-500 text-sm">
                  {phaseAgents.length} {phaseAgents.length === 1 ? 'agente' : 'agentes'}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {phaseAgents.map(agent => {
                  const isExpanded = expandedCards[agent.id];
                  return (
                    <div
                      key={agent.id}
                      className="bg-white rounded-xl border border-slate-200 p-5 hover:shadow-lg transition-shadow"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-3 flex-1">
                          <div className="p-2 bg-violet-100 rounded-lg">
                            <Bot size={24} className="text-violet-600" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <h3 className="font-semibold text-slate-900 truncate">
                              {agent.name}
                            </h3>
                            <p className="text-xs text-slate-500">
                              v{agent.version}
                            </p>
                          </div>
                        </div>
                        <button
                          onClick={() => toggleExpand(agent.id)}
                          className="text-slate-400 hover:text-slate-600"
                        >
                          {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                        </button>
                      </div>

                      <p className={`text-sm text-slate-600 mb-4 ${isExpanded ? '' : 'line-clamp-2'}`}>
                        {agent.description}
                      </p>

                      <div className="flex gap-2">
                        <button
                          onClick={() => viewAgent(agent.id)}
                          className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-slate-100 hover:bg-slate-200 rounded-lg text-sm font-medium text-slate-700 transition-colors"
                        >
                          <Eye size={16} />
                          <span>Ver Especificação</span>
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}

        {/* Agent Details Modal */}
        {viewingAgent && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-6 z-50">
            <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto p-8">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-slate-900 mb-1">
                    {viewingAgent.name}
                  </h2>
                  <p className="text-slate-600">{viewingAgent.description}</p>
                </div>
                <button
                  onClick={() => setViewingAgent(null)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <X size={24} />
                </button>
              </div>

              {/* Responsibilities */}
              <div className="mb-6">
                <h3 className="font-semibold text-slate-900 mb-3">Responsabilidades</h3>
                <ul className="space-y-2">
                  {(viewingAgent.responsibilities || []).map((resp, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-violet-600 mt-1">•</span>
                      <span className="text-slate-700">{resp}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* System Prompt */}
              <div className="mb-6">
                <h3 className="font-semibold text-slate-900 mb-3">System Prompt</h3>
                <pre className="bg-slate-50 rounded-lg p-4 text-sm text-slate-700 overflow-x-auto whitespace-pre-wrap">
                  {viewingAgent.system_prompt}
                </pre>
              </div>

              {/* Quality Criteria */}
              {viewingAgent.quality_criteria && (
                <div className="mb-6">
                  <h3 className="font-semibold text-slate-900 mb-3">Critérios de Qualidade</h3>
                  <div className="bg-yellow-50 rounded-lg p-4 space-y-2">
                    {Object.entries(viewingAgent.quality_criteria).map(([key, value]) => (
                      <div key={key} className="flex items-start gap-2">
                        <span className="font-medium text-yellow-900">{key}:</span>
                        <span className="text-yellow-800">{value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Examples */}
              {viewingAgent.examples && viewingAgent.examples.length > 0 && (
                <div>
                  <h3 className="font-semibold text-slate-900 mb-3">Exemplos</h3>
                  {viewingAgent.examples.map((example, idx) => (
                    <div key={idx} className="bg-green-50 rounded-lg p-4 mb-3">
                      <div className="mb-2">
                        <span className="font-medium text-green-900">Bom Exemplo:</span>
                        <p className="text-green-800 mt-1">{example.good_dialogue || example.good_narration}</p>
                      </div>
                      <div className="mb-2">
                        <span className="font-medium text-red-900">Mau Exemplo:</span>
                        <p className="text-red-800 mt-1">{example.bad_dialogue || example.bad_narration}</p>
                      </div>
                      <div>
                        <span className="font-medium text-slate-900">Por que é bom:</span>
                        <p className="text-slate-700 mt-1">{example.why_good}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
