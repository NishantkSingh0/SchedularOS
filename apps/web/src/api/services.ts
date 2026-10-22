import apiClient from './client'

export interface ResearchRequest {
  research_type: 'market' | 'competitors' | 'audience'
  industry?: string
  company_name?: string
  product?: string
  company_context?: string
  async_mode?: boolean
}

export interface WorkflowRunRequest {
  workflow_type: 'orchestrator' | 'marketing'
  goal: string
  industry?: string
  company_name?: string
  product?: string
  company_context?: string
  async_mode?: boolean
}

export const researchApi = {
  perform: async (data: ResearchRequest) => {
    const response = await apiClient.post('/research/perform/', data)
    return response.data
  },
}

export const workflowApi = {
  run: async (data: WorkflowRunRequest) => {
    const response = await apiClient.post('/langgraph/run/', data)
    return response.data
  },
  launch: async (goal: string) => {
    const response = await apiClient.post('/workflows/launch/', { goal })
    return response.data
  },
  list: async () => {
    const response = await apiClient.get('/workflows/')
    return response.data
  },
  detail: async (id: string) => {
    const response = await apiClient.get(`/workflows/${id}/`)
    return response.data
  },
  steps: async (runId?: string) => {
    const response = await apiClient.get('/steps/', { params: runId ? { run: runId } : {} })
    return response.data
  },
  cancel: async (id: string) => (await apiClient.post(`/workflows/${id}/cancel/`)).data,
  pause: async (id: string) => (await apiClient.post(`/workflows/${id}/pause/`)).data,
  resume: async (id: string) => (await apiClient.post(`/workflows/${id}/resume/`)).data,
}

export const knowledgeApi = {
  store: async (data: { title: string; content: string; source?: string; metadata?: any; async_mode?: boolean }) => {
    const response = await apiClient.post('/knowledge/store/', data)
    return response.data
  },
  search: async (query: string, top_k = 5) => {
    const response = await apiClient.post('/knowledge/search/', { query, top_k })
    return response.data
  },
}

export const leadsApi = {
  list: async (params?: any) => (await apiClient.get('/leads/', { params })).data,
  create: async (data: any) => (await apiClient.post('/leads/', data)).data,
  update: async (id: string, data: any) => (await apiClient.put(`/leads/${id}/`, data)).data,
}

export const proposalsApi = {
  list: async (params?: any) => (await apiClient.get('/proposals/', { params })).data,
  decide: async (id: string, data: { decision: 'approved' | 'rejected' | 'edited'; note?: string; edited_payload?: any }) =>
    (await apiClient.post(`/proposals/${id}/decide/`, data)).data,
}

export const brandsApi = {
  list: async () => (await apiClient.get('/brands/')).data,
  create: async (data: any) => (await apiClient.post('/brands/', data)).data,
}

export const agentsApi = {
  list: async () => (await apiClient.get('/agents/')).data,
  run: async (data: { agent: string; goal: string; lead_id?: string; brand_id?: string }) =>
    (await apiClient.post('/agents/run/', data)).data,
}

// Task-oriented facade — every call produces a proposal through the policy gate.
// Returns {proposal_id, status:'auto_approved'|'pending', step_id, detail?}
export const tasksApi = {
  scoreLead: (leadId: number | string, data: { score: number; rationale?: string }) =>
    apiClient.post(`/tasks/leads/${leadId}/score/`, data).then((r) => r.data),
  tagLead: (leadId: number | string, tags: string[]) =>
    apiClient.post(`/tasks/leads/${leadId}/tag/`, { tags }).then((r) => r.data),
  reply: (conversationId: number | string, body: string, rationale?: string) =>
    apiClient.post(`/tasks/conversations/${conversationId}/reply/`, { body, rationale }).then((r) => r.data),
  createCampaign: (data: { name: string; objective: string; daily_budget_paise: number; platform?: 'meta' | 'google'; target_audience?: any; rationale?: string }) =>
    apiClient.post('/tasks/advertising/campaigns/', data).then((r) => r.data),
  setCampaignStatus: (campaign_id: string, status: 'ACTIVE' | 'PAUSED') =>
    apiClient.post('/tasks/advertising/campaign-status/', { campaign_id, status }).then((r) => r.data),
  scheduleFollowup: (data: { lead_id: number; channel: 'whatsapp' | 'email'; message: string; delay_minutes?: number }) =>
    apiClient.post('/tasks/followups/schedule/', data).then((r) => r.data),
  generateCreative: (data: { kind: 'social_post' | 'ad_copy' | 'image' | 'landing_page'; brief: string; platform?: string; count?: number }) =>
    apiClient.post('/tasks/creative/generate/', data).then((r) => r.data),
  launchCampaign: (data: { name: string; objective: string; total_budget_paise: number; platforms: ('meta' | 'google')[] }) =>
    apiClient.post('/tasks/campaigns/launch/', data).then((r) => r.data),
  pipeline: () => apiClient.get('/tasks/pipeline/').then((r) => r.data),
}

export const analyticsApi = {
  kpis: async () => (await apiClient.get('/analytics/kpis/')).data,
  leadTrend: async (days = 30) => (await apiClient.get('/analytics/lead_trend/', { params: { days } })).data,
  funnel: async () => (await apiClient.get('/analytics/funnel/')).data,
  leadSources: async () => (await apiClient.get('/analytics/lead_sources/')).data,
  leadScoreDistribution: async () => (await apiClient.get('/analytics/lead_score_distribution/')).data,
  agentProductivity: async () => (await apiClient.get('/analytics/agent_productivity/')).data,
  workflowStats: async () => (await apiClient.get('/analytics/workflow_stats/')).data,
  proposalStats: async () => (await apiClient.get('/analytics/proposal_stats/')).data,
  spendOverTime: async (days = 30) => (await apiClient.get('/analytics/spend_over_time/', { params: { days } })).data,
  activity: async (limit = 50) => (await apiClient.get('/analytics/activity/', { params: { limit } })).data,
  messageTrend: async (days = 30) => (await apiClient.get('/analytics/message_trend/', { params: { days } })).data,
  trust: async () => (await apiClient.get('/analytics/trust/')).data,
  integrations: async () => (await apiClient.get('/analytics/integrations/')).data,
}
