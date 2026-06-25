import { useState, useCallback } from 'react';
import './index.css';
import Auth from './components/Auth/Auth';
import PomodoroTimer from './components/PomodoroTimer/Timer';
import ChatPanel from './components/ChatPanel/ChatPanel';
import Analytics from './components/Analytics/Analytics';

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem('novora_token'));
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('novora_user')); } catch { return null; }
  });
  const [timerEvent, setTimerEvent] = useState(null);
  const [analyticsRefresh, setAnalyticsRefresh] = useState(0);

  const handleLogin = useCallback((accessToken, userObj) => {
    setToken(accessToken);
    setUser(userObj);
    localStorage.setItem('novora_token', accessToken);
    localStorage.setItem('novora_user', JSON.stringify(userObj));
  }, []);

  const handleLogout = useCallback(() => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('novora_token');
    localStorage.removeItem('novora_user');
  }, []);

  const handleSessionStart = useCallback((state) => {
    setTimerEvent({ event: 'session_start', ...state });
  }, []);

  const handleSessionComplete = useCallback((state) => {
    setTimerEvent({ event: 'session_complete', ...state });
    setAnalyticsRefresh(n => n + 1);
  }, []);

  const handleStatusUpdate = useCallback((state) => {
    setTimerEvent(t => ({ ...t, ...state }));
  }, []);

  return (
    <>
      {/* Auth overlay when not logged in */}
      {!token && <Auth onLogin={handleLogin} />}

      <div className="app-layout">
        {/* ─── Header ─── */}
        <header className="app-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ fontSize: '1.8rem' }}>🍅</span>
            <div>
              <h1 className="text-gradient" style={{ fontSize: '1.5rem', lineHeight: 1 }}>
                Novora
              </h1>
              <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)', margin: 0 }}>
                Offline AI Pomodoro Coach
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span className="badge badge-green">● Offline</span>
            {user && (
              <>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  👤 {user.username}
                </span>
                <button
                  id="btn-logout"
                  className="btn btn-ghost"
                  onClick={handleLogout}
                  style={{ padding: '6px 14px', fontSize: '0.8rem' }}
                >
                  Sign Out
                </button>
              </>
            )}
          </div>
        </header>

        {/* ─── Timer Panel ─── */}
        <main>
          <PomodoroTimer
            onSessionStart={handleSessionStart}
            onSessionComplete={handleSessionComplete}
            onStatusUpdate={handleStatusUpdate}
          />
        </main>

        {/* ─── Chat Panel ─── */}
        <section>
          <ChatPanel
            token={token}
            timerState={timerEvent}
            onTimerCommand={handleStatusUpdate}
          />
        </section>

        {/* ─── Analytics Panel ─── */}
        <aside className="analytics-panel-wrapper">
          <Analytics
            token={token}
            refreshTrigger={analyticsRefresh}
          />
        </aside>
      </div>

      {/* Ambient background particles */}
      <div aria-hidden="true" style={{
        position: 'fixed', inset: 0, pointerEvents: 'none', zIndex: -1,
        background: `
          radial-gradient(circle at 20% 20%, rgba(124,58,237,0.06) 0%, transparent 40%),
          radial-gradient(circle at 80% 80%, rgba(6,182,212,0.04) 0%, transparent 40%)
        `,
      }} />
    </>
  );
}
