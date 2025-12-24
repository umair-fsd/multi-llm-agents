import { api } from './client'

export interface Document {
    id: string
    agent_id: string
    filename: string
    original_filename: string
    file_size: number
    mime_type: string
    status: 'pending' | 'processing' | 'completed' | 'failed'
    error_message: string | null
    chunk_count: number
    created_at: string
    processed_at: string | null
}

export interface DocumentListResponse {
    items: Document[]
    total: number
}

export const documentsApi = {
    list: (agentId?: string) => {
        const query = agentId ? `?agent_id=${agentId}` : ''
        return api.get<DocumentListResponse>(`/documents${query}`)
    },

    get: (id: string) => api.get<Document>(`/documents/${id}`),

    upload: (agentId: string, file: File) =>
        api.upload<Document>(`/documents/upload/${agentId}`, file),

    delete: (id: string) => api.delete(`/documents/${id}`),

    process: (id: string) => api.post<Document>(`/documents/${id}/process`),
}
