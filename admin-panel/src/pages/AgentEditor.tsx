import { useState, useEffect, KeyboardEvent } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
    ArrowLeft,
    Save,
    Upload,
    Trash2,
    FileText,
    Globe,
    Bot,
    Mic,
    Settings as SettingsIcon,
    CloudSun,
    Tag
} from 'lucide-react'
import { agentsApi, type Agent, type CreateAgentData } from '../api/agents'
import { documentsApi, type Document } from '../api/documents'

const defaultAgent: CreateAgentData = {
    name: '',
    description: '',
    system_prompt: 'You are a helpful AI assistant.',
    model_settings: {
        provider: 'openai',
        model_name: 'gpt-4o-mini',
        temperature: 0.7,
        max_tokens: 1024,
    },
    capabilities: {
        web_search: {
            enabled: false,
            provider: 'duckduckgo',
            max_results: 5,
        },
        weather: {
            enabled: false,
            units: 'metric',
        },
        rag: {
            enabled: false,
            collection_name: null,
            chunk_size: 1000,
            chunk_overlap: 200,
            top_k: 5,
        },
        routing_keywords: [],
        tools: [],
    },
    voice_settings: {
        tts_voice: 'aura-asteria-en',
        speaking_rate: 1.0,
    },
    is_active: true,
    is_default: false,
}

export default function AgentEditor() {
    const { id } = useParams()
    const navigate = useNavigate()
    const queryClient = useQueryClient()
    const isEditing = !!id

    const [formData, setFormData] = useState<CreateAgentData>(defaultAgent)
    const [activeTab, setActiveTab] = useState<'general' | 'capabilities' | 'documents'>('general')

    // Fetch existing agent
    const { data: agent, isLoading } = useQuery({
        queryKey: ['agent', id],
        queryFn: () => agentsApi.get(id!),
        enabled: isEditing,
    })

    // Fetch documents for this agent
    const { data: documents } = useQuery({
        queryKey: ['documents', id],
        queryFn: () => documentsApi.list(id!),
        enabled: isEditing,
    })

    // Update form when agent loads
    useEffect(() => {
        if (agent) {
            setFormData({
                name: agent.name,
                description: agent.description || '',
                system_prompt: agent.system_prompt,
                model_settings: agent.model_settings,
                capabilities: agent.capabilities,
                voice_settings: agent.voice_settings,
                is_active: agent.is_active,
                is_default: agent.is_default,
            })
        }
    }, [agent])

    // Mutations
    const createMutation = useMutation({
        mutationFn: agentsApi.create,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['agents'] })
            navigate('/agents')
        },
    })

    const updateMutation = useMutation({
        mutationFn: (data: CreateAgentData) => agentsApi.update(id!, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['agents'] })
            queryClient.invalidateQueries({ queryKey: ['agent', id] })
            navigate('/agents')
        },
    })

    const uploadMutation = useMutation({
        mutationFn: (file: File) => documentsApi.upload(id!, file),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['documents', id] })
        },
    })

    const deleteDocMutation = useMutation({
        mutationFn: documentsApi.delete,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['documents', id] })
        },
    })

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (isEditing) {
            await updateMutation.mutateAsync(formData)
        } else {
            await createMutation.mutateAsync(formData)
        }
    }

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (file) {
            await uploadMutation.mutateAsync(file)
            e.target.value = ''
        }
    }

    const isPending = createMutation.isPending || updateMutation.isPending

    if (isLoading) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}>
                <div className="spinner" />
            </div>
        )
    }

    return (
        <div>
            <div className="page-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                    <button
                        onClick={() => navigate('/agents')}
                        className="btn btn-icon btn-outline"
                    >
                        <ArrowLeft size={20} />
                    </button>
                    <div>
                        <h1 className="page-title">
                            {isEditing ? 'Edit Agent' : 'Create Agent'}
                        </h1>
                        <p className="page-subtitle">
                            {isEditing ? `Editing ${agent?.name}` : 'Configure your new AI agent'}
                        </p>
                    </div>
                </div>
                <button
                    onClick={handleSubmit}
                    className="btn btn-primary"
                    disabled={isPending || !formData.name}
                >
                    {isPending ? (
                        <div className="spinner" style={{ width: 20, height: 20 }} />
                    ) : (
                        <>
                            <Save size={20} />
                            {isEditing ? 'Save Changes' : 'Create Agent'}
                        </>
                    )}
                </button>
            </div>

            <div className="tabs">
                <button
                    className={`tab ${activeTab === 'general' ? 'active' : ''}`}
                    onClick={() => setActiveTab('general')}
                >
                    <Bot size={16} style={{ marginRight: 8 }} />
                    General
                </button>
                <button
                    className={`tab ${activeTab === 'capabilities' ? 'active' : ''}`}
                    onClick={() => setActiveTab('capabilities')}
                >
                    <SettingsIcon size={16} style={{ marginRight: 8 }} />
                    Capabilities
                </button>
                {isEditing && (
                    <button
                        className={`tab ${activeTab === 'documents' ? 'active' : ''}`}
                        onClick={() => setActiveTab('documents')}
                    >
                        <FileText size={16} style={{ marginRight: 8 }} />
                        Documents ({documents?.total || 0})
                    </button>
                )}
            </div>

            {activeTab === 'general' && (
                <div className="grid-2">
                    <div className="card">
                        <div className="card-header">
                            <h3 className="card-title">Basic Information</h3>
                        </div>
                        <div className="card-body">
                            <div className="form-group">
                                <label className="form-label">Agent Name *</label>
                                <input
                                    type="text"
                                    className="form-input"
                                    placeholder="e.g., Research Assistant"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    required
                                />
                            </div>

                            <div className="form-group">
                                <label className="form-label">Description</label>
                                <input
                                    type="text"
                                    className="form-input"
                                    placeholder="Brief description of what this agent does"
                                    value={formData.description}
                                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                />
                            </div>

                            <div className="form-group">
                                <label className="form-label">System Prompt *</label>
                                <textarea
                                    className="form-textarea code-editor"
                                    placeholder="Enter the system prompt that defines this agent's behavior..."
                                    value={formData.system_prompt}
                                    onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
                                    style={{ minHeight: 200 }}
                                />
                                <p className="form-help">
                                    This prompt defines the agent's personality, capabilities, and behavior.
                                </p>
                            </div>

                            <div className="flex gap-4">
                                <label className="toggle">
                                    <input
                                        type="checkbox"
                                        className="toggle-input"
                                        checked={formData.is_active}
                                        onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                                    />
                                    <span className="toggle-switch"></span>
                                    <span className="toggle-label">Active</span>
                                </label>

                                <label className="toggle">
                                    <input
                                        type="checkbox"
                                        className="toggle-input"
                                        checked={formData.is_default}
                                        onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
                                    />
                                    <span className="toggle-switch"></span>
                                    <span className="toggle-label">Default Agent</span>
                                </label>
                            </div>
                        </div>
                    </div>

                    <div>
                        <div className="card mb-4">
                            <div className="card-header">
                                <h3 className="card-title">Model Settings</h3>
                            </div>
                            <div className="card-body">
                                <div className="form-group">
                                    <label className="form-label">Provider</label>
                                    <select
                                        className="form-select"
                                        value={formData.model_settings?.provider}
                                        onChange={(e) => setFormData({
                                            ...formData,
                                            model_settings: { ...formData.model_settings!, provider: e.target.value as 'openai' | 'openrouter' }
                                        })}
                                    >
                                        <option value="openai">OpenAI</option>
                                        <option value="openrouter">OpenRouter</option>
                                    </select>
                                </div>

                                <div className="form-group">
                                    <label className="form-label">Model</label>
                                    <select
                                        className="form-select"
                                        value={formData.model_settings?.model_name}
                                        onChange={(e) => setFormData({
                                            ...formData,
                                            model_settings: { ...formData.model_settings!, model_name: e.target.value }
                                        })}
                                    >
                                        {formData.model_settings?.provider === 'openai' ? (
                                            <>
                                                <option value="gpt-4o">GPT-4o</option>
                                                <option value="gpt-4o-mini">GPT-4o Mini</option>
                                                <option value="gpt-4-turbo">GPT-4 Turbo</option>
                                                <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                                            </>
                                        ) : (
                                            <>
                                                <option value="openai/gpt-4o">OpenAI GPT-4o</option>
                                                <option value="anthropic/claude-3.5-sonnet">Claude 3.5 Sonnet</option>
                                                <option value="google/gemini-pro">Gemini Pro</option>
                                            </>
                                        )}
                                    </select>
                                </div>

                                <div className="form-group">
                                    <label className="form-label">
                                        Temperature: {formData.model_settings?.temperature}
                                    </label>
                                    <input
                                        type="range"
                                        min="0"
                                        max="2"
                                        step="0.1"
                                        value={formData.model_settings?.temperature}
                                        onChange={(e) => setFormData({
                                            ...formData,
                                            model_settings: { ...formData.model_settings!, temperature: parseFloat(e.target.value) }
                                        })}
                                        style={{ width: '100%' }}
                                    />
                                </div>

                                <div className="form-group">
                                    <label className="form-label">Max Tokens</label>
                                    <input
                                        type="number"
                                        className="form-input"
                                        min="1"
                                        max="8192"
                                        value={formData.model_settings?.max_tokens}
                                        onChange={(e) => setFormData({
                                            ...formData,
                                            model_settings: { ...formData.model_settings!, max_tokens: parseInt(e.target.value) }
                                        })}
                                    />
                                </div>
                            </div>
                        </div>

                        <div className="card">
                            <div className="card-header">
                                <h3 className="card-title">
                                    <Mic size={18} style={{ marginRight: 8 }} />
                                    Voice Settings
                                </h3>
                            </div>
                            <div className="card-body">
                                <div className="form-group">
                                    <label className="form-label">TTS Voice</label>
                                    <select
                                        className="form-select"
                                        value={formData.voice_settings?.tts_voice}
                                        onChange={(e) => setFormData({
                                            ...formData,
                                            voice_settings: { ...formData.voice_settings!, tts_voice: e.target.value }
                                        })}
                                    >
                                        <option value="aura-asteria-en">Asteria (Female)</option>
                                        <option value="aura-luna-en">Luna (Female)</option>
                                        <option value="aura-stella-en">Stella (Female)</option>
                                        <option value="aura-orion-en">Orion (Male)</option>
                                        <option value="aura-arcas-en">Arcas (Male)</option>
                                        <option value="aura-perseus-en">Perseus (Male)</option>
                                    </select>
                                </div>

                                <div className="form-group">
                                    <label className="form-label">
                                        Speaking Rate: {formData.voice_settings?.speaking_rate}x
                                    </label>
                                    <input
                                        type="range"
                                        min="0.5"
                                        max="2"
                                        step="0.1"
                                        value={formData.voice_settings?.speaking_rate}
                                        onChange={(e) => setFormData({
                                            ...formData,
                                            voice_settings: { ...formData.voice_settings!, speaking_rate: parseFloat(e.target.value) }
                                        })}
                                        style={{ width: '100%' }}
                                    />
                                </div>
                            </div>
                        </div>

                        <div className="card" style={{ gridColumn: '1 / -1' }}>
                            <div className="card-header">
                                <h3 className="card-title">
                                    <Tag size={18} style={{ marginRight: 8 }} />
                                    Routing Keywords
                                </h3>
                            </div>
                            <div className="card-body">
                                <p className="text-sm text-muted mb-4">
                                    Define keywords that will route user queries to this agent. Press Enter to add each keyword.
                                </p>

                                <div className="form-group">
                                    <label className="form-label">Add Keyword</label>
                                    <input
                                        type="text"
                                        className="form-input"
                                        placeholder="Type keyword and press Enter..."
                                        onKeyDown={(e: KeyboardEvent<HTMLInputElement>) => {
                                            if (e.key === 'Enter') {
                                                e.preventDefault()
                                                const input = e.currentTarget
                                                const keyword = input.value.trim().toLowerCase()
                                                if (keyword && !formData.capabilities?.routing_keywords?.includes(keyword)) {
                                                    setFormData({
                                                        ...formData,
                                                        capabilities: {
                                                            ...formData.capabilities!,
                                                            routing_keywords: [...(formData.capabilities?.routing_keywords || []), keyword]
                                                        }
                                                    })
                                                    input.value = ''
                                                }
                                            }
                                        }}
                                    />
                                    <p className="form-help">
                                        When a user's message contains any of these keywords, it will be routed to this agent.
                                    </p>
                                </div>

                                {(formData.capabilities?.routing_keywords || []).length > 0 && (
                                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 12 }}>
                                        {formData.capabilities?.routing_keywords?.map((kw, i) => (
                                            <span 
                                                key={i} 
                                                className="badge badge-info"
                                                style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}
                                                onClick={() => {
                                                    setFormData({
                                                        ...formData,
                                                        capabilities: {
                                                            ...formData.capabilities!,
                                                            routing_keywords: formData.capabilities?.routing_keywords?.filter((_, idx) => idx !== i) || []
                                                        }
                                                    })
                                                }}
                                            >
                                                {kw}
                                                <span style={{ marginLeft: 4, fontWeight: 'bold' }}>×</span>
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {activeTab === 'capabilities' && (
                <div className="grid-2">
                    <div className="card">
                        <div className="card-header">
                            <h3 className="card-title">
                                <Globe size={18} style={{ marginRight: 8 }} />
                                Web Search
                            </h3>
                            <label className="toggle">
                                <input
                                    type="checkbox"
                                    className="toggle-input"
                                    checked={formData.capabilities?.web_search.enabled}
                                    onChange={(e) => setFormData({
                                        ...formData,
                                        capabilities: {
                                            ...formData.capabilities!,
                                            web_search: { ...formData.capabilities!.web_search, enabled: e.target.checked }
                                        }
                                    })}
                                />
                                <span className="toggle-switch"></span>
                            </label>
                        </div>
                        <div className="card-body">
                            <p className="text-sm text-muted mb-4">
                                Enable the agent to search the web for real-time information.
                            </p>

                            <div className="form-group">
                                <label className="form-label">Search Provider</label>
                                <select
                                    className="form-select"
                                    value={formData.capabilities?.web_search.provider}
                                    onChange={(e) => setFormData({
                                        ...formData,
                                        capabilities: {
                                            ...formData.capabilities!,
                                            web_search: { ...formData.capabilities!.web_search, provider: e.target.value as 'tavily' | 'brave' | 'duckduckgo' }
                                        }
                                    })}
                                    disabled={!formData.capabilities?.web_search.enabled}
                                >
                                    <option value="duckduckgo">DuckDuckGo (Free)</option>
                                    <option value="tavily">Tavily (1000/month free)</option>
                                    <option value="brave">Brave (2000/month free)</option>
                                </select>
                            </div>

                            <div className="form-group">
                                <label className="form-label">Max Results</label>
                                <input
                                    type="number"
                                    className="form-input"
                                    min="1"
                                    max="20"
                                    value={formData.capabilities?.web_search.max_results}
                                    onChange={(e) => setFormData({
                                        ...formData,
                                        capabilities: {
                                            ...formData.capabilities!,
                                            web_search: { ...formData.capabilities!.web_search, max_results: parseInt(e.target.value) }
                                        }
                                    })}
                                    disabled={!formData.capabilities?.web_search.enabled}
                                />
                            </div>
                        </div>
                    </div>

                    <div className="card">
                        <div className="card-header">
                            <h3 className="card-title">
                                <CloudSun size={18} style={{ marginRight: 8 }} />
                                Weather
                            </h3>
                            <label className="toggle">
                                <input
                                    type="checkbox"
                                    className="toggle-input"
                                    checked={formData.capabilities?.weather?.enabled || false}
                                    onChange={(e) => setFormData({
                                        ...formData,
                                        capabilities: {
                                            ...formData.capabilities!,
                                            weather: { ...formData.capabilities!.weather, enabled: e.target.checked }
                                        }
                                    })}
                                />
                                <span className="toggle-switch"></span>
                            </label>
                        </div>
                        <div className="card-body">
                            <p className="text-sm text-muted mb-4">
                                Enable the agent to get real-time weather information using OpenWeatherMap.
                            </p>

                            <div className="form-group">
                                <label className="form-label">Temperature Units</label>
                                <select
                                    className="form-select"
                                    value={formData.capabilities?.weather?.units || 'metric'}
                                    onChange={(e) => setFormData({
                                        ...formData,
                                        capabilities: {
                                            ...formData.capabilities!,
                                            weather: { ...formData.capabilities!.weather, units: e.target.value as 'metric' | 'imperial' }
                                        }
                                    })}
                                    disabled={!formData.capabilities?.weather?.enabled}
                                >
                                    <option value="metric">Celsius (°C)</option>
                                    <option value="imperial">Fahrenheit (°F)</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div className="card">
                        <div className="card-header">
                            <h3 className="card-title">
                                <FileText size={18} style={{ marginRight: 8 }} />
                                RAG (Document Q&A)
                            </h3>
                            <label className="toggle">
                                <input
                                    type="checkbox"
                                    className="toggle-input"
                                    checked={formData.capabilities?.rag.enabled}
                                    onChange={(e) => setFormData({
                                        ...formData,
                                        capabilities: {
                                            ...formData.capabilities!,
                                            rag: { ...formData.capabilities!.rag, enabled: e.target.checked }
                                        }
                                    })}
                                />
                                <span className="toggle-switch"></span>
                            </label>
                        </div>
                        <div className="card-body">
                            <p className="text-sm text-muted mb-4">
                                Enable the agent to answer questions based on uploaded documents.
                            </p>

                            <div className="form-group">
                                <label className="form-label">Chunk Size</label>
                                <input
                                    type="number"
                                    className="form-input"
                                    min="100"
                                    max="4000"
                                    value={formData.capabilities?.rag.chunk_size}
                                    onChange={(e) => setFormData({
                                        ...formData,
                                        capabilities: {
                                            ...formData.capabilities!,
                                            rag: { ...formData.capabilities!.rag, chunk_size: parseInt(e.target.value) }
                                        }
                                    })}
                                    disabled={!formData.capabilities?.rag.enabled}
                                />
                                <p className="form-help">Size of text chunks for embedding (100-4000)</p>
                            </div>

                            <div className="form-group">
                                <label className="form-label">Top K Results</label>
                                <input
                                    type="number"
                                    className="form-input"
                                    min="1"
                                    max="20"
                                    value={formData.capabilities?.rag.top_k}
                                    onChange={(e) => setFormData({
                                        ...formData,
                                        capabilities: {
                                            ...formData.capabilities!,
                                            rag: { ...formData.capabilities!.rag, top_k: parseInt(e.target.value) }
                                        }
                                    })}
                                    disabled={!formData.capabilities?.rag.enabled}
                                />
                                <p className="form-help">Number of relevant chunks to retrieve</p>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {activeTab === 'documents' && isEditing && (
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">Uploaded Documents</h3>
                        <label className="btn btn-primary" style={{ cursor: 'pointer' }}>
                            <Upload size={20} />
                            Upload PDF
                            <input
                                type="file"
                                accept=".pdf,.txt,.docx"
                                onChange={handleFileUpload}
                                style={{ display: 'none' }}
                                disabled={uploadMutation.isPending}
                            />
                        </label>
                    </div>

                    {!documents?.items.length ? (
                        <div className="empty-state">
                            <FileText className="empty-state-icon" size={64} />
                            <h4 className="empty-state-title">No documents uploaded</h4>
                            <p className="empty-state-description">
                                Upload PDF documents to enable RAG-based Q&A for this agent
                            </p>
                        </div>
                    ) : (
                        <table>
                            <thead>
                                <tr>
                                    <th>Filename</th>
                                    <th>Size</th>
                                    <th>Status</th>
                                    <th>Chunks</th>
                                    <th>Uploaded</th>
                                    <th style={{ width: 80 }}></th>
                                </tr>
                            </thead>
                            <tbody>
                                {documents.items.map((doc) => (
                                    <tr key={doc.id}>
                                        <td>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                                <FileText size={20} style={{ color: 'var(--gray-400)' }} />
                                                {doc.original_filename}
                                            </div>
                                        </td>
                                        <td>{(doc.file_size / 1024).toFixed(1)} KB</td>
                                        <td>
                                            <span className={`badge badge-${doc.status === 'completed' ? 'success' : doc.status === 'failed' ? 'error' : 'warning'}`}>
                                                {doc.status}
                                            </span>
                                        </td>
                                        <td>{doc.chunk_count}</td>
                                        <td>{new Date(doc.created_at).toLocaleDateString()}</td>
                                        <td>
                                            <button
                                                className="btn btn-icon btn-outline"
                                                onClick={() => deleteDocMutation.mutate(doc.id)}
                                                disabled={deleteDocMutation.isPending}
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            )}
        </div>
    )
}
