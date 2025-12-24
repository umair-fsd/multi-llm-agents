import { useQuery } from '@tanstack/react-query'
import {
    Database,
    Cpu,
    Globe,
    Mic,
    CheckCircle,
    XCircle,
    ExternalLink
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
    }
    voice: {
        tts_voices: string[]
    }
}

export default function Settings() {
    const { data, isLoading } = useQuery({
        queryKey: ['settings'],
        queryFn: () => api.get<SettingsResponse>('/settings'),
    })

    const { data: health } = useQuery({
        queryKey: ['health'],
        queryFn: () => api.get<{ status: string; services: Record<string, string> }>('/settings/health'),
        refetchInterval: 30000, // Refresh every 30s
    })

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
                                    <label className="form-label">Default Provider</label>
                                    <div className="badge badge-info" style={{ display: 'inline-flex' }}>
                                        {data?.search.default_provider}
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label className="form-label">Available Providers</label>
                                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                                        {data?.search.providers.map((p) => (
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
                                        {data?.voice.tts_voices.slice(0, 6).map((v) => (
                                            <span key={v} className="badge badge-gray" style={{ fontSize: '0.7rem' }}>
                                                {v.replace('aura-', '').replace('-en', '')}
                                            </span>
                                        ))}
                                        {(data?.voice.tts_voices.length || 0) > 6 && (
                                            <span className="badge badge-gray">+{(data?.voice.tts_voices.length || 0) - 6} more</span>
                                        )}
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
