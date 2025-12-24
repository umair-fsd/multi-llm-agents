import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { MessageSquare, Clock, User, Eye, XCircle, ChevronLeft, Wrench, Bot } from 'lucide-react'
import { api } from '../api/client'

interface Message {
    id: string
    role: string
    content: string
    agent_id: string | null
    agent_name: string | null
    tools_used: string[]
    created_at: string
}

interface Session {
    id: string
    user_id: string | null
    room_name: string | null
    participant_name: string | null
    status: string
    started_at: string
    ended_at: string | null
    message_count: number
    metadata: Record<string, unknown>
}

interface SessionDetail extends Session {
    messages: Message[]
}

interface SessionListResponse {
    items: Session[]
    total: number
    page: number
    page_size: number
}

export default function Sessions() {
    const [selectedId, setSelectedId] = useState<string | null>(null)
    const [statusFilter, setStatusFilter] = useState<string>('')
    const queryClient = useQueryClient()

    const { data, isLoading, error } = useQuery({
        queryKey: ['sessions', statusFilter],
        queryFn: () => api.get<SessionListResponse>(`/sessions${statusFilter ? `?status_filter=${statusFilter}` : ''}`),
    })

    const { data: sessionDetail, isLoading: detailLoading, refetch: refetchDetail } = useQuery({
        queryKey: ['session', selectedId],
        queryFn: () => api.get<SessionDetail>(`/sessions/${selectedId}`),
        enabled: !!selectedId,
    })

    const endSessionMutation = useMutation({
        mutationFn: async (sessionId: string) => {
            return await api.post(`/sessions/${sessionId}/end`, { reason: 'Admin ended session' })
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['sessions'] })
            if (selectedId) {
                queryClient.invalidateQueries({ queryKey: ['session', selectedId] })
                refetchDetail()
            }
        },
        onError: (err) => {
            console.error('Failed to end session:', err)
            alert('Failed to end session: ' + (err as Error).message)
        },
    })

    const deleteSessionMutation = useMutation({
        mutationFn: (sessionId: string) => api.delete(`/sessions/${sessionId}`),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['sessions'] })
            setSelectedId(null)
        },
    })

    // Session Detail View
    if (selectedId && sessionDetail) {
        return (
            <div>
                <div className="page-header">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                        <button 
                            className="btn btn-secondary"
                            onClick={() => setSelectedId(null)}
                            style={{ padding: '0.5rem' }}
                        >
                            <ChevronLeft size={20} />
                        </button>
                        <div>
                            <h1 className="page-title">Session Details</h1>
                            <p className="page-subtitle">
                                {sessionDetail.participant_name || 'Unknown'} • {sessionDetail.room_name}
                            </p>
                        </div>
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                        {sessionDetail.status === 'active' && (
                            <button 
                                className="btn btn-danger"
                                onClick={() => endSessionMutation.mutate(sessionDetail.id)}
                                disabled={endSessionMutation.isPending}
                            >
                                <XCircle size={16} />
                                End Session
                            </button>
                        )}
                        <button 
                            className="btn btn-secondary"
                            onClick={() => {
                                if (confirm('Delete this session and all messages?')) {
                                    deleteSessionMutation.mutate(sessionDetail.id)
                                }
                            }}
                            disabled={deleteSessionMutation.isPending}
                        >
                            Delete
                        </button>
                    </div>
                </div>

                {/* Session Info Cards */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
                    <div className="card">
                        <div className="card-body" style={{ padding: '1rem' }}>
                            <div style={{ fontSize: '0.75rem', color: 'var(--gray-500)', marginBottom: '0.25rem' }}>Participant</div>
                            <div style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                <User size={16} />
                                {sessionDetail.participant_name || 'Unknown'}
                            </div>
                        </div>
                    </div>
                    <div className="card">
                        <div className="card-body" style={{ padding: '1rem' }}>
                            <div style={{ fontSize: '0.75rem', color: 'var(--gray-500)', marginBottom: '0.25rem' }}>Status</div>
                            <span className={`badge ${sessionDetail.status === 'active' ? 'badge-success' : 'badge-gray'}`}>
                                {sessionDetail.status}
                            </span>
                        </div>
                    </div>
                    <div className="card">
                        <div className="card-body" style={{ padding: '1rem' }}>
                            <div style={{ fontSize: '0.75rem', color: 'var(--gray-500)', marginBottom: '0.25rem' }}>Messages</div>
                            <div style={{ fontWeight: 600 }}>{sessionDetail.message_count}</div>
                        </div>
                    </div>
                    <div className="card">
                        <div className="card-body" style={{ padding: '1rem' }}>
                            <div style={{ fontSize: '0.75rem', color: 'var(--gray-500)', marginBottom: '0.25rem' }}>Duration</div>
                            <div style={{ fontWeight: 600 }}>
                                {sessionDetail.ended_at
                                    ? `${Math.round((new Date(sessionDetail.ended_at).getTime() - new Date(sessionDetail.started_at).getTime()) / 1000 / 60)} min`
                                    : 'Ongoing'}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Agents & Tools Used */}
                {sessionDetail.metadata && (
                    <div className="card" style={{ marginBottom: '1.5rem' }}>
                        <div className="card-body" style={{ padding: '1rem' }}>
                            <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
                                {sessionDetail.metadata.agents_used && (
                                    <div>
                                        <div style={{ fontSize: '0.75rem', color: 'var(--gray-500)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                            <Bot size={14} /> Agents Used
                                        </div>
                                        <div style={{ display: 'flex', gap: '0.25rem', flexWrap: 'wrap' }}>
                                            {(sessionDetail.metadata.agents_used as string[]).map(agent => (
                                                <span key={agent} className="badge badge-info">{agent}</span>
                                            ))}
                                        </div>
                                    </div>
                                )}
                                {sessionDetail.metadata.tools_used && (sessionDetail.metadata.tools_used as string[]).length > 0 && (
                                    <div>
                                        <div style={{ fontSize: '0.75rem', color: 'var(--gray-500)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                            <Wrench size={14} /> Tools Used
                                        </div>
                                        <div style={{ display: 'flex', gap: '0.25rem', flexWrap: 'wrap' }}>
                                            {(sessionDetail.metadata.tools_used as string[]).map(tool => (
                                                <span key={tool} className="badge badge-warning">{tool}</span>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* Conversation */}
                <div className="card">
                    <div className="card-header">
                        <h3>Conversation</h3>
                    </div>
                    <div className="card-body" style={{ padding: 0 }}>
                        {detailLoading ? (
                            <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}>
                                <div className="spinner" />
                            </div>
                        ) : !sessionDetail.messages.length ? (
                            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--gray-500)' }}>
                                No messages in this session
                            </div>
                        ) : (
                            <div style={{ maxHeight: '500px', overflowY: 'auto' }}>
                                {sessionDetail.messages.map((msg, i) => (
                                    <div 
                                        key={msg.id} 
                                        style={{ 
                                            padding: '1rem 1.5rem',
                                            borderBottom: i < sessionDetail.messages.length - 1 ? '1px solid var(--gray-100)' : 'none',
                                            background: msg.role === 'user' ? 'var(--gray-50)' : 'white',
                                        }}
                                    >
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                <span className={`badge ${msg.role === 'user' ? 'badge-info' : 'badge-success'}`}>
                                                    {msg.role === 'user' ? 'User' : msg.agent_name || 'AI'}
                                                </span>
                                                {msg.tools_used && msg.tools_used.length > 0 && (
                                                    <span className="badge badge-warning" style={{ fontSize: '0.65rem' }}>
                                                        <Wrench size={10} style={{ marginRight: 2 }} />
                                                        {msg.tools_used.join(', ')}
                                                    </span>
                                                )}
                                            </div>
                                            <span style={{ fontSize: '0.75rem', color: 'var(--gray-400)' }}>
                                                {new Date(msg.created_at).toLocaleTimeString()}
                                            </span>
                                        </div>
                                        <p style={{ margin: 0, lineHeight: 1.5 }}>{msg.content}</p>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        )
    }

    // Sessions List View
    return (
        <div>
            <div className="page-header">
                <div>
                    <h1 className="page-title">Sessions</h1>
                    <p className="page-subtitle">
                        Voice conversation history
                    </p>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <select 
                        value={statusFilter} 
                        onChange={(e) => setStatusFilter(e.target.value)}
                        className="form-select"
                        style={{ padding: '0.5rem 1rem', borderRadius: '0.5rem', border: '1px solid var(--gray-200)' }}
                    >
                        <option value="">All Sessions</option>
                        <option value="active">Active Only</option>
                        <option value="ended">Ended Only</option>
                    </select>
                </div>
            </div>

            <div className="table-container">
                {isLoading ? (
                    <div className="card-body" style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}>
                        <div className="spinner" />
                    </div>
                ) : error ? (
                    <div className="card-body" style={{ textAlign: 'center', padding: '3rem', color: 'var(--error)' }}>
                        Failed to load sessions. Is the backend running?
                    </div>
                ) : !data?.items.length ? (
                    <div className="empty-state">
                        <MessageSquare className="empty-state-icon" size={64} />
                        <h4 className="empty-state-title">No sessions yet</h4>
                        <p className="empty-state-description">
                            Voice sessions will appear here once users start interacting with agents
                        </p>
                    </div>
                ) : (
                    <table>
                        <thead>
                            <tr>
                                <th>Participant</th>
                                <th>Room</th>
                                <th>Messages</th>
                                <th>Started</th>
                                <th>Duration</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data.items.map((session) => (
                                <tr key={session.id}>
                                    <td>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                            <User size={16} style={{ color: 'var(--gray-400)' }} />
                                            {session.participant_name || 'Unknown'}
                                        </div>
                                    </td>
                                    <td>
                                        <code style={{
                                            fontSize: '0.75rem',
                                            background: 'var(--gray-100)',
                                            padding: '2px 8px',
                                            borderRadius: 4
                                        }}>
                                            {session.room_name?.slice(0, 20) || '-'}
                                        </code>
                                    </td>
                                    <td>
                                        <span className="badge badge-info">
                                            {session.message_count}
                                        </span>
                                    </td>
                                    <td>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                            <Clock size={14} style={{ color: 'var(--gray-400)' }} />
                                            {new Date(session.started_at).toLocaleString()}
                                        </div>
                                    </td>
                                    <td>
                                        {session.ended_at
                                            ? `${Math.round((new Date(session.ended_at).getTime() - new Date(session.started_at).getTime()) / 1000 / 60)} min`
                                            : '-'}
                                    </td>
                                    <td>
                                        <span className={`badge ${session.status === 'active' ? 'badge-success' : 'badge-gray'}`}>
                                            {session.status}
                                        </span>
                                    </td>
                                    <td>
                                        <div style={{ display: 'flex', gap: '0.25rem' }}>
                                            <button 
                                                className="btn btn-secondary" 
                                                style={{ padding: '0.25rem 0.5rem' }}
                                                onClick={() => setSelectedId(session.id)}
                                            >
                                                <Eye size={14} />
                                            </button>
                                            {session.status === 'active' && (
                                                <button 
                                                    className="btn btn-danger" 
                                                    style={{ padding: '0.25rem 0.5rem' }}
                                                    onClick={() => endSessionMutation.mutate(session.id)}
                                                    disabled={endSessionMutation.isPending}
                                                >
                                                    <XCircle size={14} />
                                                </button>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    )
}
