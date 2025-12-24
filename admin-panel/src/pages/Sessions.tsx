import { useQuery } from '@tanstack/react-query'
import { MessageSquare, Clock, User } from 'lucide-react'
import { api } from '../api/client'

interface Session {
    id: string
    user_id: string | null
    room_name: string | null
    started_at: string
    ended_at: string | null
    message_count: number
}

interface SessionListResponse {
    items: Session[]
    total: number
    page: number
    page_size: number
}

export default function Sessions() {
    const { data, isLoading, error } = useQuery({
        queryKey: ['sessions'],
        queryFn: () => api.get<SessionListResponse>('/sessions'),
    })

    return (
        <div>
            <div className="page-header">
                <div>
                    <h1 className="page-title">Sessions</h1>
                    <p className="page-subtitle">
                        Voice conversation history
                    </p>
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
                                <th>Session ID</th>
                                <th>Room</th>
                                <th>Messages</th>
                                <th>Started</th>
                                <th>Duration</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data.items.map((session) => (
                                <tr key={session.id}>
                                    <td>
                                        <code style={{
                                            fontSize: '0.75rem',
                                            background: 'var(--gray-100)',
                                            padding: '2px 8px',
                                            borderRadius: 4
                                        }}>
                                            {session.id.slice(0, 8)}...
                                        </code>
                                    </td>
                                    <td>{session.room_name || '-'}</td>
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
                                        <span className={`badge ${session.ended_at ? 'badge-gray' : 'badge-success'}`}>
                                            {session.ended_at ? 'Ended' : 'Active'}
                                        </span>
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
