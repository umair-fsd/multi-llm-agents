import { useQuery } from '@tanstack/react-query'
import {
    Bot,
    MessageSquare,
    FileText,
    Activity,
    TrendingUp,
    Clock
} from 'lucide-react'
import { agentsApi } from '../api/agents'

export default function Dashboard() {
    const { data: agentsData, isLoading } = useQuery({
        queryKey: ['agents'],
        queryFn: () => agentsApi.list(),
    })

    const stats = [
        {
            label: 'Total Agents',
            value: agentsData?.total || 0,
            icon: Bot,
            color: 'blue',
        },
        {
            label: 'Active Agents',
            value: agentsData?.items.filter(a => a.is_active).length || 0,
            icon: Activity,
            color: 'green',
        },
        {
            label: 'Total Sessions',
            value: 0,
            icon: MessageSquare,
            color: 'purple',
        },
        {
            label: 'Documents',
            value: agentsData?.items.reduce((sum, a) => sum + a.document_count, 0) || 0,
            icon: FileText,
            color: 'yellow',
        },
    ]

    return (
        <div>
            <div className="page-header">
                <div>
                    <h1 className="page-title">Dashboard</h1>
                    <p className="page-subtitle">Overview of your AI agents and activity</p>
                </div>
            </div>

            <div className="stat-cards">
                {stats.map((stat) => (
                    <div key={stat.label} className="stat-card">
                        <div className={`stat-card-icon ${stat.color}`}>
                            <stat.icon size={24} />
                        </div>
                        <div className="stat-card-content">
                            <div className="stat-card-label">{stat.label}</div>
                            <div className="stat-card-value">
                                {isLoading ? '...' : stat.value}
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            <div className="grid-2">
                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">
                            <TrendingUp size={18} style={{ marginRight: 8, verticalAlign: 'middle' }} />
                            Agent Activity
                        </h3>
                        <span className="text-sm text-muted">Last 7 days</span>
                    </div>
                    <div className="card-body">
                        <div className="empty-state">
                            <Activity className="empty-state-icon" size={48} />
                            <h4 className="empty-state-title">No activity yet</h4>
                            <p className="empty-state-description">
                                Start a voice session to see activity metrics here
                            </p>
                        </div>
                    </div>
                </div>

                <div className="card">
                    <div className="card-header">
                        <h3 className="card-title">
                            <Clock size={18} style={{ marginRight: 8, verticalAlign: 'middle' }} />
                            Recent Sessions
                        </h3>
                        <a href="/sessions" className="text-sm" style={{ color: 'var(--primary-500)' }}>
                            View All
                        </a>
                    </div>
                    <div className="card-body">
                        <div className="empty-state">
                            <MessageSquare className="empty-state-icon" size={48} />
                            <h4 className="empty-state-title">No sessions yet</h4>
                            <p className="empty-state-description">
                                Voice sessions will appear here once users start interacting
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
