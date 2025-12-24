import { api } from './client'

export interface ModelSettings {
    provider: 'openai' | 'openrouter'
    model_name: string
    temperature: number
    max_tokens: number
}

export interface WebSearchConfig {
    enabled: boolean
    provider: 'tavily' | 'brave' | 'duckduckgo'
    max_results: number
}

export interface RAGConfig {
    enabled: boolean
    collection_name: string | null
    chunk_size: number
    chunk_overlap: number
    top_k: number
}

export interface VoiceSettings {
    tts_voice: string
    speaking_rate: number
}

export interface AgentCapabilities {
    web_search: WebSearchConfig
    rag: RAGConfig
    tools: string[]
}

export interface Agent {
    id: string
    name: string
    description: string | null
    system_prompt: string
    model_settings: ModelSettings
    capabilities: AgentCapabilities
    voice_settings: VoiceSettings
    is_active: boolean
    is_default: boolean
    document_count: number
    created_at: string
    updated_at: string
}

export interface AgentListResponse {
    items: Agent[]
    total: number
    page: number
    page_size: number
}

export interface CreateAgentData {
    name: string
    description?: string
    system_prompt: string
    model_settings?: Partial<ModelSettings>
    capabilities?: Partial<AgentCapabilities>
    voice_settings?: Partial<VoiceSettings>
    is_active?: boolean
    is_default?: boolean
}

export const agentsApi = {
    list: (params?: { page?: number; page_size?: number; is_active?: boolean }) => {
        const searchParams = new URLSearchParams()
        if (params?.page) searchParams.set('page', String(params.page))
        if (params?.page_size) searchParams.set('page_size', String(params.page_size))
        if (params?.is_active !== undefined) searchParams.set('is_active', String(params.is_active))

        const query = searchParams.toString()
        return api.get<AgentListResponse>(`/agents${query ? `?${query}` : ''}`)
    },

    get: (id: string) => api.get<Agent>(`/agents/${id}`),

    create: (data: CreateAgentData) => api.post<Agent>('/agents', data),

    update: (id: string, data: Partial<CreateAgentData>) =>
        api.patch<Agent>(`/agents/${id}`, data),

    delete: (id: string) => api.delete(`/agents/${id}`),
}
