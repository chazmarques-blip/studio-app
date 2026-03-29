import { useState } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Sparkles, Check, X, Loader } from 'lucide-react';
import { CharacterApprovalStep } from './CharacterApprovalStep';
import { FinalCheckpointDashboard } from './FinalCheckpointDashboard';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/**
 * Autonomous Agents Workflow Manager
 * Manages the autonomous loop flow with character approval and final checkpoint
 */
export function AutonomousWorkflow({ 
  projectId,
  characters = [],
  onComplete,
  onCancel 
}) {
  const [phase, setPhase] = useState('character_approval'); // 'character_approval' | 'loop_running' | 'final_checkpoint'
  const [loopStatus, setLoopStatus] = useState(null);
  const [checkpoint, setCheckpoint] = useState(null);
  const [loopRunning, setLoopRunning] = useState(false);

  // Start autonomous loop after character approval
  const handleCharacterApproval = async (approvedChars) => {
    try {
      setPhase('loop_running');
      setLoopRunning(true);

      // 1. Create Bible with approved characters
      await axios.post(`${API}/studio/projects/${projectId}/create-bible`);
      
      // 2. Start autonomous loop
      const { data } = await axios.post(`${API}/studio/autonomous-loop/start`, {
        project_id: projectId,
        user_prompt: "Continue development with approved characters"
      });

      setLoopStatus(data);
      
      // 3. Poll for completion
      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await axios.get(`${API}/studio/autonomous-loop/status/${projectId}`);
          
          if (statusRes.data.ready_for_approval) {
            clearInterval(pollInterval);
            setLoopRunning(false);
            
            // Load final checkpoint
            const checkpointRes = await axios.get(`${API}/studio/projects/${projectId}/bible`);
            const costRes = await axios.get(`${API}/studio/projects/${projectId}/cost-estimate`);
            
            setCheckpoint({
              bible: checkpointRes.data.bible,
              estimate: costRes.data.estimate
            });
            
            setPhase('final_checkpoint');
            toast.success('Loop autônomo concluído! Revise o resultado.');
          }
        } catch (error) {
          console.error('Poll error:', error);
        }
      }, 5000); // Poll every 5 seconds

    } catch (error) {
      console.error('Error starting loop:', error);
      toast.error('Erro ao iniciar loop autônomo');
      setLoopRunning(false);
      setPhase('character_approval');
    }
  };

  // User approved final checkpoint
  const handleFinalApproval = () => {
    toast.success('Projeto aprovado! Iniciando produção de vídeos...');
    onComplete(checkpoint);
  };

  // User wants to adjust
  const handleFinalReject = () => {
    toast.info('Voltando para ajustes...');
    setPhase('character_approval');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 p-6">
      {/* Character Approval Phase */}
      {phase === 'character_approval' && (
        <CharacterApprovalStep
          projectId={projectId}
          characters={characters}
          onApprove={handleCharacterApproval}
          onCancel={onCancel}
        />
      )}

      {/* Loop Running Phase */}
      {phase === 'loop_running' && (
        <div className="max-w-2xl mx-auto mt-20">
          <div className="bg-white rounded-2xl p-12 text-center">
            <Loader size={64} className="text-violet-600 animate-spin mx-auto mb-6" />
            <h2 className="text-3xl font-bold text-slate-900 mb-4">
              Agentes Trabalhando...
            </h2>
            <p className="text-slate-600 mb-6">
              Os agentes especializados estão criando diálogos cinematográficos, narração poética
              e refinando o projeto até atingir quality score {'>'}= 90%.
            </p>
            
            {loopStatus && (
              <div className="space-y-3">
                <div className="flex items-center justify-between px-6 py-3 bg-slate-50 rounded-lg">
                  <span className="text-sm text-slate-700">Iteração</span>
                  <span className="font-bold text-violet-600">{loopStatus.iterations || 1} / 5</span>
                </div>
                <div className="flex items-center justify-between px-6 py-3 bg-slate-50 rounded-lg">
                  <span className="text-sm text-slate-700">Quality Score</span>
                  <span className="font-bold text-violet-600">{loopStatus.quality_score || 0}%</span>
                </div>
              </div>
            )}

            <p className="text-xs text-slate-500 mt-8">
              Isso pode levar 2-5 minutos dependendo da complexidade
            </p>
          </div>
        </div>
      )}

      {/* Final Checkpoint Phase */}
      {phase === 'final_checkpoint' && checkpoint && (
        <FinalCheckpointDashboard
          projectId={projectId}
          checkpoint={checkpoint}
          onApprove={handleFinalApproval}
          onReject={handleFinalReject}
        />
      )}
    </div>
  );
}
