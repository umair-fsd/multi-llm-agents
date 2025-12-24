import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
    Plus,
    Search,
    MoreVertical,
    Edit,
    Trash2,
    Eye,
    Bot,
    Globe,
    FileText
} from 'lucide-react'
import { agentsApi, type Agent } from '../api/agents'

export default function AgentList() {
    const queryClient = useQueryClient()
    const [searchQuery, setSearchQuery] = useState('')

    const { data, isLoading, error } = useQuery({
        queryKey: ['agents'],
        queryFn: () => agentsApi.list({ page_size: 50 }),
    })

    const deleteMutation = useMutation({
        mutationFn: agentsApi.delete,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['agents'] })
        },
    })

    const handleDelete = async (agent: Agent) => {
        if (confirm(`Are you sure you want to delete "${agent.name}"?`)) {
            await deleteMutation.mutateAsync(agent.id)
        }
    }

    const filteredAgents = data?.items.filter(agent =>
        agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        agent.description?.toLowerCase().includes(searchQuery.toLowerCase())
    ) || []

    return (
        <div>
            <div className="page-header">
                <div>
                    <h1 className="page-title">Agents</h1>
                    <p className="page-subtitle">
                        {data?.total || 0} agents in total
                    </p>
                </div>
                <Link to="/agents/new" className="btn btn-primary">
                    <Plus size={20} />
                    Add Agent
                </Link>
            </div>

            <div className="table-container">
                <div className="table-header">
                    <div className="table-search" style={{ position: 'relative' }}>
                        <Search size={18} className="table-search-icon" style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)' }} />
                        <input
                            type="text"
                            className="table-search-input"
                            placeholder="Search agents by name or description..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            style={{ paddingLeft: 40 }}
                        />
                    </div>
                </div>

                {isLoading ? (
                    <div className="card-body" style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}>
                        <div className="spinner" />
                    </div>
                ) : error ? (
                    <div className="card-body" style={{ textAlign: 'center', padding: '3rem', color: 'var(--error)' }}>
                        Failed to load agents. Is the backend running?
                    </div>
                ) : filteredAgents.length === 0 ? (
                    <div className="empty-state">
                        <Bot className="empty-state-icon" size={64} />
                        <h4 className="empty-state-title">No agents yet</h4>
                        <p className="empty-state-description">
                            Create your first AI agent to get started
                        </p>
                        <Link to="/agents/new" className="btn btn-primary">
                            <Plus size={20} />
                            Create Agent
                        </Link>
                    </div>
                ) : (
                    <table>
                        <thead>
                            <tr>
                                <th>Agent</th>
                                <th>Model</th>
                                <th>Capabilities</th>
                                <th>Documents</th>
                                <th>Status</th>
                                <th style={{ width: 100 }}></th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredAgents.map((agent) => (
                                <tr key={agent.id}>
                                    <td>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                            <div style={{
                                                width: 40,
                                                height: 40,
                                                borderRadius: 8,
                                                background: 'var(--primary-100)',
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                color: 'var(--primary-600)'
                                            }}>
                                                <Bot size={20} />
                                            </div>
                                            <div>
                                                <div style={{ fontWeight: 600, color: 'var(--gray-800)' }}>
                                                    {agent.name}
                                                    {agent.is_default && (
                                                        <span className="badge badge-info" style={{ marginLeft: 8 }}>Default</span>
                                                    )}
                                                </div>
                                                <div className="text-sm text-muted">
                                                    {agent.description || 'No description'}
                                                </div>
                                            </div>
                                        </div>
                                    </td>
                                    <td>
                                        <div className="text-sm">
                                            <div style={{ fontWeight: 500 }}>{agent.model_settings.model_name}</div>
                                            <div className="text-muted">{agent.model_settings.provider}</div>
                                        </div>
                                    </td>
                                    <td>
                                        <div style={{ display: 'flex', gap: 8 }}>
                                            {agent.capabilities.web_search.enabled && (
                                                <span className="badge badge-info" title="Web Search">
                                                    <Globe size={12} style={{ marginRight: 4 }} />
                                                    Search
                                                </span>
                                            )}
                                            {agent.capabilities.rag.enabled && (
                                                <span className="badge badge-success" title="RAG">
                                                    <FileText size={12} style={{ marginRight: 4 }} />
                                                    RAG
                                                </span>
                                            )}
                                            {!agent.capabilities.web_search.enabled && !agent.capabilities.rag.enabled && (
                                                <span className="badge badge-gray">Base</span>
                                            )}
                                        </div>
                                    </td>
                                    <td>
                                        <span className={agent.document_count > 0 ? 'badge badge-success' : 'badge badge-gray'}>
                                            {agent.document_count}
                                        </span>
                                    </td>
                                    <td>
                                        <span className={agent.is_active ? 'badge badge-success' : 'badge badge-gray'}>
                                            {agent.is_active ? 'Active' : 'Inactive'}
                                        </span>
                                    </td>
                                    <td>
                                        <div style={{ display: 'flex', gap: 4 }}>
                                            <Link
                                                to={`/agents/${agent.id}`}
                                                className="btn btn-icon btn-outline"
                                                title="Edit"
                                            >
                                                <Edit size={16} />
                                            </Link>
                                            <button
                                                className="btn btn-icon btn-outline"
                                                title="Delete"
                                                onClick={() => handleDelete(agent)}
                                                disabled={deleteMutation.isPending}
                                            >
                                                <Trash2 size={16} />
                                            </button>
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
