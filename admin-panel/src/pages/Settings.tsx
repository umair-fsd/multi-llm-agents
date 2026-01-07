import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
    Database,
    Cpu,
    Globe,
    Mic,
    Volume2,
    CheckCircle,
    XCircle,
    ExternalLink,
    Save,
    RefreshCw
} from 'lucide-react'
import { api } from '../api/client'

interface ProviderInfo {
    name: string
    configured: boolean
    models?: string[]
    voices?: string[]
}

interface SettingsResponse {
    environment: string
    llm: {
        default_provider: string
        default_model: string
        providers: Record<string, ProviderInfo>
    }
    tts: {
        default_provider: string
        default_voice: string
        providers: Record<string, ProviderInfo>
    }
    stt: {
        default_provider: string
        providers: Record<string, ProviderInfo>
    }
    search: {
        default_provider: string
        providers: Record<string, ProviderInfo>
    }
}

export default function Settings() {
    const queryClient = useQueryClient()
    
    // LLM state
    const [llmProvider, setLlmProvider] = useState('')
    const [llmModel, setLlmModel] = useState('')
    
    // TTS state
    const [ttsProvider, setTtsProvider] = useState('')
    const [ttsVoice, setTtsVoice] = useState('')
    
    // STT state
    const [sttProvider, setSttProvider] = useState('')
    
    // Search state
    const [searchProvider, setSearchProvider] = useState('')

    const { data, isLoading, refetch } = useQuery({
        queryKey: ['settings'],
        queryFn: () => api.get<SettingsResponse>('/settings'),
    })

    const { data: health, refetch: refetchHealth } = useQuery({
        queryKey: ['health'],
        queryFn: () => api.get<{ status: string; services: Record<string, string> }>('/settings/health'),
        refetchInterval: 30000,
    })

    // Initialize state when data loads
    useEffect(() => {
        if (data) {
            setLlmProvider(data.llm.default_provider)
            setLlmModel(data.llm.default_model)
            setTtsProvider(data.tts.default_provider)
            setTtsVoice(data.tts.default_voice)
            setSttProvider(data.stt.default_provider)
            setSearchProvider(data.search.default_provider)
        }
    }, [data])

    // Mutations
    const saveSetting = useMutation({
        mutationFn: async ({ endpoint, value }: { endpoint: string; value: string }) => {
            return api.put(`/settings/${endpoint}`, { value })
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['settings'] })
        },
        onError: (error) => {
            alert('Failed to save: ' + (error as Error).message)
        },
    })

    const handleSave = (endpoint: string, value: string, label: string) => {
        saveSetting.mutate({ endpoint, value }, {
            onSuccess: () => {
                alert(`${label} updated successfully!`)
            }
        })
    }

    // Get available models/voices for selected provider
    const llmModels = data?.llm.providers[llmProvider]?.models || []
    const ttsVoices = data?.tts.providers[ttsProvider]?.voices || []

    const ProviderCard = ({ 
        title, 
        icon: Icon, 
        providers, 
        selectedProvider, 
        setSelectedProvider, 
        selectedOption,
        setSelectedOption,
        optionLabel,
        options,
        providerEndpoint,
        optionEndpoint,
        defaultProvider,
        defaultOption,
    }: {
        title: string
        icon: React.ComponentType<{ size: number; style?: React.CSSProperties }>
        providers: Record<string, ProviderInfo>
        selectedProvider: string
        setSelectedProvider: (v: string) => void
        selectedOption?: string
        setSelectedOption?: (v: string) => void
        optionLabel?: string
        options?: string[]
        providerEndpoint: string
        optionEndpoint?: string
        defaultProvider: string
        defaultOption?: string
    }) => (
        <div className="card">
            <div className="card-header">
                <h3 className="card-title">
                    <Icon size={18} style={{ marginRight: 8 }} />
                    {title}
                </h3>
            </div>
            <div className="card-body">
                {/* Provider Selection */}
                <div className="form-group">
                    <label className="form-label">Provider</label>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        <select
                            value={selectedProvider}
                            onChange={(e) => {
                                setSelectedProvider(e.target.value)
                                // Reset option to first available
                                if (setSelectedOption && options) {
                                    const newOptions = providers[e.target.value]?.voices || 
                                                       providers[e.target.value]?.models || []
                                    if (newOptions.length > 0) {
                                        setSelectedOption(newOptions[0])
                                    }
                                }
                            }}
                            className="form-select"
                            style={{ flex: 1 }}
                        >
                            {Object.entries(providers).map(([key, info]) => (
                                <option 
                                    key={key} 
                                    value={key}
                                    disabled={!info.configured}
                                >
                                    {info.name}
                                    {!info.configured && ' (not configured)'}
                                </option>
                            ))}
                        </select>
                        <button
                            className="btn btn-primary"
                            onClick={() => handleSave(providerEndpoint, selectedProvider, title + ' Provider')}
                            disabled={saveSetting.isPending || selectedProvider === defaultProvider}
                        >
                            <Save size={16} />
                        </button>
                    </div>
                    {selectedProvider !== defaultProvider && (
                        <p className="text-warning text-sm mt-1">Unsaved changes</p>
                    )}
                </div>

                {/* Option Selection (Model/Voice) */}
                {optionLabel && setSelectedOption && options && (
                    <div className="form-group mt-3">
                        <label className="form-label">{optionLabel}</label>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                            <select
                                value={selectedOption}
                                onChange={(e) => setSelectedOption(e.target.value)}
                                className="form-select"
                                style={{ flex: 1 }}
                                disabled={selectedProvider !== defaultProvider}
                            >
                                {options.map((opt) => (
                                    <option key={opt} value={opt}>{opt}</option>
                                ))}
                            </select>
                            {optionEndpoint && (
                                <button
                                    className="btn btn-primary"
                                    onClick={() => handleSave(optionEndpoint, selectedOption!, optionLabel)}
                                    disabled={
                                        saveSetting.isPending || 
                                        selectedOption === defaultOption ||
                                        selectedProvider !== defaultProvider
                                    }
                                >
                                    <Save size={16} />
                                </button>
                            )}
                        </div>
                        {selectedProvider !== defaultProvider && (
                            <p className="text-muted text-sm mt-1">Save provider first</p>
                        )}
                        {selectedProvider === defaultProvider && selectedOption !== defaultOption && (
                            <p className="text-warning text-sm mt-1">Unsaved changes</p>
                        )}
                    </div>
                )}

                {/* API Key Status */}
                <div className="form-group mt-3">
                    <label className="form-label">API Keys</label>
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                        {Object.entries(providers).map(([key, info]) => (
                            <span 
                                key={key} 
                                className={`badge ${info.configured ? 'badge-success' : 'badge-gray'}`}
                                style={{ display: 'flex', alignItems: 'center', gap: 4 }}
                            >
                                {info.configured ? <CheckCircle size={12} /> : <XCircle size={12} />}
                                {key}
                            </span>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    )

    if (isLoading) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
                <div className="spinner" />
            </div>
        )
    }

    return (
        <div>
            <div className="page-header">
                <div>
                    <h1 className="page-title">Settings</h1>
                    <p className="page-subtitle">
                        Configure AI providers for voice, text, and search
                    </p>
                </div>
                <button 
                    className="btn btn-secondary" 
                    onClick={() => { refetch(); refetchHealth(); }}
                >
                    <RefreshCw size={16} />
                    Refresh
                </button>
            </div>

            {/* Service Status */}
            <div className="card mb-4">
                <div className="card-header">
                    <h3 className="card-title">
                        <Database size={18} style={{ marginRight: 8 }} />
                        Service Status
                    </h3>
                </div>
                <div className="card-body">
                    {health ? (
                        <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
                            {Object.entries(health.services).map(([name, status]) => (
                                <div key={name} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <CheckCircle size={16} style={{ color: 'var(--success)' }} />
                                    <span style={{ textTransform: 'capitalize', fontWeight: 500 }}>{name}</span>
                                    <span className="text-muted text-sm">({status})</span>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="spinner" />
                    )}
                </div>
            </div>

            {/* Provider Cards */}
            <div className="grid-2">
                {/* LLM Provider */}
                {data && (
                    <ProviderCard
                        title="LLM (Language Model)"
                        icon={Cpu}
                        providers={data.llm.providers}
                        selectedProvider={llmProvider}
                        setSelectedProvider={setLlmProvider}
                        selectedOption={llmModel}
                        setSelectedOption={setLlmModel}
                        optionLabel="Model"
                        options={llmModels}
                        providerEndpoint="llm-provider"
                        optionEndpoint="llm-model"
                        defaultProvider={data.llm.default_provider}
                        defaultOption={data.llm.default_model}
                    />
                )}

                {/* TTS Provider */}
                {data && (
                    <ProviderCard
                        title="TTS (Text-to-Speech)"
                        icon={Volume2}
                        providers={data.tts.providers}
                        selectedProvider={ttsProvider}
                        setSelectedProvider={setTtsProvider}
                        selectedOption={ttsVoice}
                        setSelectedOption={setTtsVoice}
                        optionLabel="Voice"
                        options={ttsVoices}
                        providerEndpoint="tts-provider"
                        optionEndpoint="tts-voice"
                        defaultProvider={data.tts.default_provider}
                        defaultOption={data.tts.default_voice}
                    />
                )}

                {/* STT Provider */}
                {data && (
                    <ProviderCard
                        title="STT (Speech-to-Text)"
                        icon={Mic}
                        providers={data.stt.providers}
                        selectedProvider={sttProvider}
                        setSelectedProvider={setSttProvider}
                        providerEndpoint="stt-provider"
                        defaultProvider={data.stt.default_provider}
                    />
                )}

                {/* Search Provider */}
                {data && (
                    <ProviderCard
                        title="Web Search"
                        icon={Globe}
                        providers={data.search.providers}
                        selectedProvider={searchProvider}
                        setSelectedProvider={setSearchProvider}
                        providerEndpoint="search-provider"
                        defaultProvider={data.search.default_provider}
                    />
                )}
            </div>

            {/* Quick Links */}
            <div className="card mt-4">
                <div className="card-header">
                    <h3 className="card-title">Quick Links</h3>
                </div>
                <div className="card-body">
                    <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                        <a
                            href="http://localhost:8000/docs"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn btn-outline"
                        >
                            <ExternalLink size={16} />
                            API Docs
                        </a>
                        <a
                            href="http://localhost:6333/dashboard"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn btn-outline"
                        >
                            <ExternalLink size={16} />
                            Qdrant
                        </a>
                        <a
                            href="https://console.groq.com/keys"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn btn-outline"
                        >
                            <ExternalLink size={16} />
                            Groq (FREE)
                        </a>
                        <a
                            href="https://console.deepgram.com/"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn btn-outline"
                        >
                            <ExternalLink size={16} />
                            Deepgram
                        </a>
                    </div>
                </div>
            </div>
        </div>
    )
}
