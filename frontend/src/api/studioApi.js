/**
 * Studio API — All studio-related HTTP calls in one place.
 * Components import from here instead of building URLs manually.
 */
import api from './client';

export const studioApi = {
  // Projects
  listProjects: () => api.get('/studio/projects'),
  getProjectStatus: (id) => api.get(`/studio/projects/${id}/status`),
  createProject: (data) => api.post('/studio/projects', data),
  deleteProject: (id) => api.delete(`/studio/projects/${id}`),

  // Storyboard
  getStoryboard: (projectId) => api.get(`/studio/projects/${projectId}/storyboard`),
  generateStoryboard: (projectId, data) => api.post(`/studio/projects/${projectId}/generate-storyboard`, data),
  regeneratePanel: (projectId, data) => api.post(`/studio/projects/${projectId}/storyboard/regenerate-panel`, data),
  editPanel: (projectId, data) => api.patch(`/studio/projects/${projectId}/storyboard/edit-panel`, data),
  approveStoryboard: (projectId) => api.patch(`/studio/projects/${projectId}/storyboard/approve`, { approved: true }),

  // Continuity
  analyzeContinuity: (projectId, data) => api.post(`/studio/projects/${projectId}/continuity/analyze`, data),

  // Production
  startProduction: (projectId, data) => api.post(`/studio/projects/${projectId}/production/start`, data),
  getProductionStatus: (projectId) => api.get(`/studio/projects/${projectId}/production/status`),

  // Post-production
  uploadAudio: (projectId, formData) => api.post(`/studio/projects/${projectId}/post-production/audio`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  deleteAudio: (projectId, sceneNumber) => api.delete(`/studio/projects/${projectId}/post-production/audio/${sceneNumber}`),
  startPostProduction: (projectId, data) => api.post(`/studio/projects/${projectId}/post-production/start`, data),

  // Smart Editor
  smartEdit: (projectId, data) => api.post(`/studio/projects/${projectId}/smart-editor/edit`, data),

  // Export
  generatePdf: (projectId) => api.post(`/studio/projects/${projectId}/export/pdf`),
  generateBook: (projectId) => api.post(`/studio/projects/${projectId}/export/book`),

  // Language
  generateLanguageVersion: (projectId, data) => api.post(`/studio/projects/${projectId}/language/generate`, data),

  // Chat
  storyboardChat: (projectId, data) => api.post(`/studio/projects/${projectId}/storyboard/chat`, data),

  // Characters
  uploadAvatar: (projectId, formData) => api.post(`/studio/projects/${projectId}/characters/avatar`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),

  // Cache
  getCacheStats: () => api.get('/studio/cache/stats'),
  flushCache: () => api.post('/studio/cache/flush'),
};
