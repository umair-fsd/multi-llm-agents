import { useState, useCallback, useEffect } from 'react'
import {
  LiveKitRoom,
  RoomAudioRenderer,
  useVoiceAssistant,
  BarVisualizer,
  useLocalParticipant,
  useTracks,
} from '@livekit/components-react'
import { Track } from 'livekit-client'
import '@livekit/components-styles'
import './index.css'

const LIVEKIT_URL = import.meta.env.VITE_LIVEKIT_URL || 'ws://localhost:7880'
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Microphone visualizer component
function MicrophoneVisualizer() {
  const tracks = useTracks([Track.Source.Microphone], { onlySubscribed: false })
  const localMicTrack = tracks.find(t => t.participant?.isLocal)

  if (!localMicTrack) {
    return (
      <div className="mic-indicator mic-indicator--inactive">
        <div className="mic-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
            <line x1="12" y1="19" x2="12" y2="23" />
            <line x1="8" y1="23" x2="16" y2="23" />
          </svg>
        </div>
      </div>
    )
  }

  return (
    <div className="mic-indicator mic-indicator--active">
      <BarVisualizer 
        trackRef={localMicTrack} 
        barCount={5}
        options={{ minHeight: 4 }}
      />
    </div>
  )
}

// Main voice interface component
function VoiceInterface({ onDisconnect }: { onDisconnect: () => void }) {
  const { state, audioTrack } = useVoiceAssistant()
  const { isMicrophoneEnabled } = useLocalParticipant()
  
  // Determine current state
  const isConnecting = state === 'connecting'
  const isListening = state === 'listening'
  const isThinking = state === 'thinking'
  const isSpeaking = state === 'speaking'
  const isIdle = !isConnecting && !isListening && !isThinking && !isSpeaking

  // Get status info
  const getStatusInfo = () => {
    if (isConnecting) return { label: 'Connecting...', color: 'yellow' }
    if (isSpeaking) return { label: 'AI Speaking', color: 'violet' }
    if (isThinking) return { label: 'Thinking...', color: 'emerald' }
    if (isListening) return { label: 'Listening', color: 'cyan' }
    return { label: 'Ready', color: 'gray' }
  }

  const status = getStatusInfo()

  return (
    <div className="voice-interface">
      {/* Main AI Orb */}
      <div className="main-orb-container">
        <div className={`main-orb main-orb--${status.color} ${isSpeaking || isThinking ? 'main-orb--active' : ''}`}>
          {/* Inner glow */}
          <div className="main-orb__glow" />
          
          {/* Core */}
          <div className="main-orb__core">
            {isSpeaking && audioTrack ? (
              <div className="orb-visualizer">
                <BarVisualizer 
                  state={state} 
                  barCount={5} 
                  trackRef={audioTrack}
                  options={{ minHeight: 8 }}
                />
              </div>
            ) : isThinking ? (
              <div className="thinking-animation">
                <span /><span /><span />
              </div>
            ) : (
              <div className="orb-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                  <line x1="12" y1="19" x2="12" y2="23" />
                  <line x1="8" y1="23" x2="16" y2="23" />
                </svg>
              </div>
            )}
          </div>

          {/* Animated rings */}
          <div className="main-orb__rings">
            <div className="ring ring--1" />
            <div className="ring ring--2" />
            <div className="ring ring--3" />
          </div>
        </div>

        {/* Status label */}
        <div className={`status-label status-label--${status.color}`}>
          <span className="status-dot" />
          {status.label}
        </div>
      </div>

      {/* Your microphone section */}
      <div className="mic-section">
        <div className="mic-section__header">
          <span className="mic-section__title">Your Microphone</span>
          <span className={`mic-status ${isMicrophoneEnabled ? 'mic-status--on' : 'mic-status--off'}`}>
            {isMicrophoneEnabled ? 'Active' : 'Inactive'}
          </span>
        </div>
        <MicrophoneVisualizer />
      </div>

      {/* Instructions */}
      <div className="instructions">
        {isSpeaking ? (
          <>🔊 AI is responding...</>
        ) : isThinking ? (
          <>🧠 Processing your request...</>
        ) : isListening ? (
          <>🎤 Speak now – I'm listening</>
        ) : (
          <>💬 Say something to begin</>
        )}
      </div>

      {/* End button */}
      <button onClick={onDisconnect} className="btn btn--end">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
        End Session
      </button>

      <RoomAudioRenderer />
    </div>
  )
}

// Connection form component
function ConnectForm({ 
  onConnect, 
  loading, 
  error 
}: { 
  onConnect: (name: string) => void
  loading: boolean
  error: string
}) {
  const [name, setName] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (name.trim()) {
      onConnect(name.trim())
    }
  }

  return (
    <form onSubmit={handleSubmit} className="connect-form">
      <div className="logo-section">
        <div className="logo-orb">
          <div className="main-orb main-orb--violet main-orb--idle">
            <div className="main-orb__glow" />
            <div className="main-orb__core">
              <div className="orb-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                  <line x1="12" y1="19" x2="12" y2="23" />
                  <line x1="8" y1="23" x2="16" y2="23" />
                </svg>
              </div>
            </div>
            <div className="main-orb__rings">
              <div className="ring ring--1" />
              <div className="ring ring--2" />
            </div>
          </div>
        </div>
        <h1>Voice AI</h1>
        <p className="tagline">Intelligent conversation, naturally spoken</p>
      </div>

      <div className="form-card">
        <div className="input-group">
          <label htmlFor="name">Your Name</label>
          <input
            id="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter your name"
            autoComplete="name"
            autoFocus
          />
        </div>

        <button 
          type="submit" 
          className="btn btn--primary"
          disabled={loading || !name.trim()}
        >
          {loading ? (
            <span className="spinner" />
          ) : (
            <>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="5 3 19 12 5 21 5 3" />
              </svg>
              Start Conversation
            </>
          )}
        </button>

        {error && (
          <div className="error-message">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            {error}
          </div>
        )}
      </div>

      <div className="features">
        <div className="feature">
          <span className="feature__icon">🎯</span>
          <span>Dynamic AI routing</span>
        </div>
        <div className="feature">
          <span className="feature__icon">⚡</span>
          <span>Real-time responses</span>
        </div>
        <div className="feature">
          <span className="feature__icon">🔒</span>
          <span>Private & secure</span>
        </div>
      </div>
    </form>
  )
}

// Main App component
function App() {
  const [token, setToken] = useState('')
  const [roomName, setRoomName] = useState('')
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  // Generate room name on mount
  useEffect(() => {
    setRoomName(`room-${Date.now()}`)
  }, [])

  const handleConnect = useCallback(async (username: string) => {
    setLoading(true)
    setError('')

    try {
      const url = `${API_URL}/api/v1/livekit/token?room=${encodeURIComponent(roomName)}&identity=${encodeURIComponent(username)}`
      const response = await fetch(url)

      if (!response.ok) {
        throw new Error('Connection failed. Please check if the server is running.')
      }

      const data = await response.json()
      setToken(data.token)
      setConnected(true)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to connect'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [roomName])

  const handleDisconnect = useCallback(() => {
    setConnected(false)
    setToken('')
    setError('')
    setRoomName(`room-${Date.now()}`)
  }, [])

  return (
    <div className="app">
      <div className="background">
        <div className="background__gradient" />
        <div className="background__noise" />
      </div>

      <main className="main">
        {!connected ? (
          <ConnectForm 
            onConnect={handleConnect}
            loading={loading}
            error={error}
          />
        ) : (
          <LiveKitRoom
            token={token}
            serverUrl={LIVEKIT_URL}
            connect={true}
            audio={true}
            video={false}
            className="livekit-room"
          >
            <VoiceInterface onDisconnect={handleDisconnect} />
          </LiveKitRoom>
        )}
      </main>

      <footer className="footer">
        <span>Powered by AI</span>
      </footer>
    </div>
  )
}

export default App
