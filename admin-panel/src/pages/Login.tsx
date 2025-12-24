import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Zap, LogIn, Eye, EyeOff } from 'lucide-react'
import { useAuthStore } from '../stores/authStore'

export default function Login() {
    const navigate = useNavigate()
    const { login } = useAuthStore()
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [showPassword, setShowPassword] = useState(false)
    const [loading, setLoading] = useState(false)

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)

        try {
            await login(email, password)
            navigate('/')
        } catch (error) {
            console.error('Login failed:', error)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="login-page">
            <div className="login-left">
                <div className="login-brand">
                    <div className="login-brand-icon">
                        <Zap size={28} />
                    </div>
                    <div>
                        <div className="login-brand-text">Agentic AI</div>
                        <div className="login-brand-subtitle">Admin Portal</div>
                    </div>
                </div>

                <div className="login-tagline">Nice to see you again</div>
                <h1 className="login-title">WELCOME<br />BACK</h1>
                <p className="login-description">
                    Sign in to access your dashboard, manage AI agents,
                    configure voice interactions, and monitor conversations.
                </p>
            </div>

            <div className="login-right">
                <div className="login-form-container">
                    <h2 className="login-form-title">Login Account</h2>
                    <p className="login-form-subtitle">Enter your credentials to continue</p>

                    <form className="login-form" onSubmit={handleSubmit}>
                        <div className="form-group">
                            <label className="form-label" htmlFor="email">
                                Email Address
                            </label>
                            <input
                                id="email"
                                type="email"
                                className="form-input"
                                placeholder="name@company.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label className="form-label" htmlFor="password">
                                Password
                                <a href="#" className="forgot-link">Forgot password?</a>
                            </label>
                            <div style={{ position: 'relative' }}>
                                <input
                                    id="password"
                                    type={showPassword ? 'text' : 'password'}
                                    className="form-input"
                                    placeholder="••••••••"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                    style={{ paddingRight: '48px' }}
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    style={{
                                        position: 'absolute',
                                        right: '12px',
                                        top: '50%',
                                        transform: 'translateY(-50%)',
                                        background: 'none',
                                        border: 'none',
                                        color: 'var(--gray-400)',
                                        cursor: 'pointer',
                                    }}
                                >
                                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                                </button>
                            </div>
                        </div>

                        <button
                            type="submit"
                            className="btn btn-primary"
                            disabled={loading}
                        >
                            {loading ? (
                                <span className="spinner" style={{ width: 20, height: 20 }} />
                            ) : (
                                <>
                                    <LogIn size={20} />
                                    Sign In
                                </>
                            )}
                        </button>
                    </form>
                </div>

                <div className="login-footer">
                    © 2024 Voice Agentic AI. All rights reserved.
                </div>
            </div>
        </div>
    )
}
