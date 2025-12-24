import { NavLink } from 'react-router-dom'
import {
    LayoutDashboard,
    Bot,
    MessageSquare,
    Settings,
    Zap
} from 'lucide-react'
import { useAuthStore } from '../stores/authStore'

const navItems = [
    {
        section: 'Overview',
        items: [
            { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
        ],
    },
    {
        section: 'Agent Management',
        items: [
            { icon: Bot, label: 'Agents', path: '/agents' },
            { icon: MessageSquare, label: 'Sessions', path: '/sessions' },
        ],
    },
    {
        section: 'Configuration',
        items: [
            { icon: Settings, label: 'Settings', path: '/settings' },
        ],
    },
]

export default function Sidebar() {
    const { user } = useAuthStore()

    return (
        <aside className="sidebar">
            <div className="sidebar-logo">
                <div className="sidebar-logo-icon">
                    <Zap size={24} />
                </div>
                <div>
                    <div className="sidebar-logo-text">Agentic AI</div>
                </div>
            </div>

            <nav className="sidebar-nav">
                {navItems.map((section) => (
                    <div key={section.section} className="sidebar-section">
                        <div className="sidebar-section-title">{section.section}</div>
                        {section.items.map((item) => (
                            <NavLink
                                key={item.path}
                                to={item.path}
                                className={({ isActive }) =>
                                    `sidebar-link ${isActive ? 'active' : ''}`
                                }
                                end={item.path === '/'}
                            >
                                <item.icon size={20} />
                                {item.label}
                            </NavLink>
                        ))}
                    </div>
                ))}
            </nav>

            <div className="sidebar-user">
                <div className="sidebar-user-avatar">
                    {user?.name?.charAt(0).toUpperCase() || 'A'}
                </div>
                <div className="sidebar-user-info">
                    <div className="sidebar-user-name">{user?.name || 'Admin'}</div>
                    <div className="sidebar-user-role">Administrator</div>
                </div>
            </div>
        </aside>
    )
}
