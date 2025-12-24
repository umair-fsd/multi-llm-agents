import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
    Database,
    Cpu,
    Globe,
    Mic,
    CheckCircle,
    ExternalLink,
    Save
} from 'lucide-react'
import { api } from '../api/client'

interface SettingsResponse {
    environment: string
    llm: {
        default_provider: string
        default_model: string
        providers: string[]
        models: Record<string, string[]>
    }
    search: {
        default_provider: string
        providers: string[]
        api_keys_configured: Record<string, boolean>
    }
    voice: {
        tts_voices: string[]
    }
}

export default function Settings() {
    const queryClient = useQueryClient()
    const [selectedSearchProvider, setSelectedSearchProvider] = useState<string>('')

    const { data, isLoading } = useQuery({
        queryKey: ['settings'],
        queryFn: () => api.get<SettingsResponse>('/settings'),
        onSuccess: (data) => {
            setSelectedSearchProvider(data.search.default_provider)
        },
    })

    const { data: health } = useQuery({
        queryKey: ['health'],
        queryFn: () => api.get<{ status: string; services: Record<string, string> }>('/settings/health'),
        refetchInterval: 30000,
    })

    const updateSearchProviderMutation = useMutation({
        mutationFn: (provider: string) => 
            api.put('/settings/search-provider', { value: provider }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['settings'] })
            alert('Search provider updated successfully!')
        },
        onError: (error) => {
            alert('Failed to update: ' + (error as Error).message)
        },
    })

    // Set initial value when data loads
    if (data && !selectedSearchProvider) {
        setSelectedSearchProvider(data.search.default_provider)
    }

    const handleSaveSearchProvider = () => {
        if (selectedSearchProvider && selectedSearchProvider !== data?.search.default_provider) {
            updateSearchProviderMutation.mutate(selectedSearchProvider)
        }
    }

    return (
        <div>
            <div className="page-header">
                <div>
                    <h1 className="page-title">Settings</h1>
                    <p className="page-subtitle">
                        System configuration and service status
                    </p>
                </div>
            </div>

            <div className="grid-2">
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">
                            <Database size={18} style={{ marginRight: 8 }} />
                            Service Status
                        </h3>
                    </div>
                    <div className="card-body">
                        {health ? (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                                {Object.entries(health.services).map(([name, status]) => (
                                    <div key={name} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <span style={{ textTransform: 'capitalize', fontWeight: 500 }}>{name}</span>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                            <span className="text-sm text-muted">{status}</span>
                                            <CheckCircle size={18} style={{ color: 'var(--success)' }} />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}>
                                <div className="spinner" />
                            </div>
                        )}
                    </div>
                </div>

                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">
                            <Cpu size={18} style={{ marginRight: 8 }} />
                            LLM Configuration
                        </h3>
                    </div>
                    <div className="card-body">
                        {isLoading ? (
                            <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}>
                                <div className="spinner" />
                            </div>
                        ) : (
                            <>
                                <div className="form-group">
                                    <label className="form-label">Default Provider</label>
                                    <div className="badge badge-info" style={{ display: 'inline-flex' }}>
                                        {data?.llm.default_provider}
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Default Model</label>
                                    <div className="badge badge-success" style={{ display: 'inline-flex' }}>
                                        {data?.llm.default_model}
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Available Providers</label>
                                    <div style={{ display: 'flex', gap: 8 }}>
                                        {data?.llm.providers.map((p) => (
                                            <span key={p} className="badge badge-gray">{p}</span>
                                        ))}
                                    </div>
                                </div>
                            </>
                        )}
                    </div>
                </div>

                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">
                            <Globe size={18} style={{ marginRight: 8 }} />
                            Web Search
                        </h3>
                    </div>
                    <div className="card-body">
                        {isLoading ? (
                            <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}>
                                <div className="spinner" />
                            </div>
                        ) : (
                            <>
                                <div className="form-group">
                                    <label className="form-label">Search Provider</label>
                                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                                        <select
                                            value={selectedSearchProvider}
                                            onChange={(e) => setSelectedSearchProvider(e.target.value)}
                                            style={{
                                                padding: '0.5rem 1rem',
                                                borderRadius: '0.5rem',
                                                border: '1px solid var(--gray-200)',
                                                flex: 1,
                                            }}
                                        >
                                            {data?.search.providers.map((p) => (
                                                <option 
                                                    key={p} 
                                                    value={p}
                                                    disabled={!data.search.api_keys_configured[p]}
                                                >
                                                    {p.charAt(0).toUpperCase() + p.slice(1)}
                                                    {!data.search.api_keys_configured[p] && ' (API key not set)'}
                                                </option>
                                            ))}
                                        </select>
                                        <button
                                            className="btn btn-primary"
                                            onClick={handleSaveSearchProvider}
                                            disabled={
                                                updateSearchProviderMutation.isPending || 
                                                selectedSearchProvider === data?.search.default_provider
                                            }
                                        >
                                            <Save size={16} />
                                            Save
                                        </button>
                                    </div>
                                    {selectedSearchProvider !== data?.search.default_provider && (
                                        <p style={{ fontSize: '0.75rem', color: 'var(--warning)', marginTop: '0.5rem' }}>
                                            Click Save to apply changes
                                        </p>
                                    )}
                                </div>
                                <div className="form-group">
                                    <label className="form-label">API Keys Status</label>
                                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                                        {data?.search.providers.map((p) => (
                                            <span 
                                                key={p} 
                                                className={`badge ${data.search.api_keys_configured[p] ? 'badge-success' : 'badge-gray'}`}
                                            >
                                                {p}: {data.search.api_keys_configured[p] ? '✓ Configured' : 'Not set'}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            </>
                        )}
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
                        {isLoading ? (
                            <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}>
                                <div className="spinner" />
                            </div>
                        ) : (
                            <>
                                <div className="form-group">
                                    <label className="form-label">Available TTS Voices</label>
                                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                                        {data?.voice.tts_voices.map((v) => (
                                            <span key={v} className="badge badge-gray" style={{ fontSize: '0.7rem' }}>
                                                {v}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            </>
                        )}
                    </div>
                </div>
            </div>

            <div className="card mt-4">
                <div className="card-header">
                    <h3 className="card-title">Quick Links</h3>
                </div>
                <div className="card-body">
                    <div style={{ display: 'flex', gap: 16 }}>
                        <a
                            href="http://localhost:8000/docs"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn btn-outline"
                        >
                            <ExternalLink size={18} />
                            API Documentation
                        </a>
                        <a
                            href="http://localhost:6333/dashboard"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn btn-outline"
                        >
                            <ExternalLink size={18} />
                            Qdrant Dashboard
                        </a>
                    </div>
                </div>
            </div>
        </div>
    )
}
