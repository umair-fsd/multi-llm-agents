import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
    id: string
    email: string
    name: string
    isAdmin: boolean
}

interface AuthState {
    user: User | null
    isAuthenticated: boolean
    login: (email: string, password: string) => Promise<void>
    logout: () => void
}

// Dummy auth store - will be replaced with real auth later
export const useAuthStore = create<AuthState>()(
    persist(
        (set) => ({
            user: null,
            isAuthenticated: false,

            login: async (email: string, _password: string) => {
                // Dummy login - accepts any credentials
                const user: User = {
                    id: '00000000-0000-0000-0000-000000000001',
                    email: email,
                    name: email.split('@')[0],
                    isAdmin: true,
                }
                set({ user, isAuthenticated: true })
            },

            logout: () => {
                set({ user: null, isAuthenticated: false })
            },
        }),
        {
            name: 'auth-storage',
        }
    )
)
