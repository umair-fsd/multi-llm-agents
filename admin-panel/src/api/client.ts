const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

class ApiClient {
    private baseUrl: string

    constructor() {
        this.baseUrl = `${API_URL}/api/v1`
    }

    private async request<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<T> {
        const url = `${this.baseUrl}${endpoint}`

        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        })

        if (!response.ok) {
            const error = await response.json().catch(() => ({}))
            throw new Error(error.detail || `HTTP ${response.status}`)
        }

        if (response.status === 204) {
            return null as T
        }

        return response.json()
    }

    async get<T>(endpoint: string): Promise<T> {
        return this.request<T>(endpoint, { method: 'GET' })
    }

    async post<T>(endpoint: string, data?: unknown): Promise<T> {
        return this.request<T>(endpoint, {
            method: 'POST',
            body: data ? JSON.stringify(data) : undefined,
        })
    }

    async patch<T>(endpoint: string, data: unknown): Promise<T> {
        return this.request<T>(endpoint, {
            method: 'PATCH',
            body: JSON.stringify(data),
        })
    }

    async put<T>(endpoint: string, data: unknown): Promise<T> {
        return this.request<T>(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data),
        })
    }

    async delete(endpoint: string): Promise<void> {
        return this.request<void>(endpoint, { method: 'DELETE' })
    }

    async upload<T>(endpoint: string, file: File): Promise<T> {
        const formData = new FormData()
        formData.append('file', file)

        const response = await fetch(`${this.baseUrl}${endpoint}`, {
            method: 'POST',
            body: formData,
        })

        if (!response.ok) {
            const error = await response.json().catch(() => ({}))
            throw new Error(error.detail || `HTTP ${response.status}`)
        }

        return response.json()
    }
}

export const api = new ApiClient()
