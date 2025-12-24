import { Bell, RefreshCw, LogOut } from 'lucide-react'
import { useAuthStore } from '../stores/authStore'

export default function Header() {
    const { user, logout } = useAuthStore()

    return (
        <header className="header">
            <div className="header-left">
                <span className="header-welcome">
                    Welcome back, <strong>{user?.name || 'Admin'}</strong>!
                </span>
                <span className="header-badge">
                    <span>🤖</span> Voice Agentic AI
                </span>
            </div>

            <div className="header-right">
                <button className="header-icon-btn" title="Refresh">
                    <RefreshCw size={20} />
                </button>
                <button className="header-icon-btn" title="Notifications">
                    <Bell size={20} />
                    <span className="badge">3</span>
                </button>
                <button
                    className="header-icon-btn"
                    title="Logout"
                    onClick={logout}
                >
                    <LogOut size={20} />
                </button>
                <div className="header-avatar">
                    {user?.name?.charAt(0).toUpperCase() || 'A'}
                </div>
            </div>
        </header>
    )
}
