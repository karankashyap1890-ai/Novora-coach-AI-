import { useState } from 'react';
import './Auth.css';

const API_BASE = 'http://localhost:8000';

export default function Auth({ onLogin }) {
  const [tab, setTab] = useState('login');
  const [form, setForm] = useState({ username: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = e => {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }));
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const endpoint = tab === 'login' ? '/auth/login' : '/auth/register';
    const body = tab === 'login'
      ? { username: form.username, password: form.password }
      : { username: form.username, email: form.email, password: form.password };

    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || 'Something went wrong. Please try again.');
      } else {
        onLogin(data.access_token, data.user);
      }
    } catch {
      setError('Cannot connect to Novora backend. Make sure it\'s running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-overlay">
      <div className="glass-card auth-card">
        <div className="auth-logo">
          <span className="auth-logo-icon">🍅</span>
          <div className="auth-logo-name text-gradient">Novora</div>
          <div className="auth-logo-tagline">Your offline AI Pomodoro coach</div>
        </div>

        {/* Tabs */}
        <div className="auth-tabs">
          <button
            className={`auth-tab ${tab === 'login' ? 'active' : ''}`}
            onClick={() => setTab('login')}
            id="tab-login"
          >Sign In</button>
          <button
            className={`auth-tab ${tab === 'register' ? 'active' : ''}`}
            onClick={() => setTab('register')}
            id="tab-register"
          >Create Account</button>
        </div>

        {/* Form */}
        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          <div className="auth-field">
            <label className="auth-label" htmlFor="auth-username">Username</label>
            <input
              id="auth-username"
              className="auth-input"
              type="text"
              name="username"
              placeholder="your_username"
              value={form.username}
              onChange={handleChange}
              required
              minLength={3}
              maxLength={50}
              autoComplete="username"
            />
          </div>

          {tab === 'register' && (
            <div className="auth-field">
              <label className="auth-label" htmlFor="auth-email">Email</label>
              <input
                id="auth-email"
                className="auth-input"
                type="email"
                name="email"
                placeholder="you@example.com"
                value={form.email}
                onChange={handleChange}
                required
                autoComplete="email"
              />
            </div>
          )}

          <div className="auth-field">
            <label className="auth-label" htmlFor="auth-password">Password</label>
            <input
              id="auth-password"
              className="auth-input"
              type="password"
              name="password"
              placeholder={tab === 'login' ? '••••••••' : 'Min 8 chars, include a number'}
              value={form.password}
              onChange={handleChange}
              required
              minLength={8}
              autoComplete={tab === 'login' ? 'current-password' : 'new-password'}
            />
          </div>

          {error && <div className="auth-error" role="alert">⚠️ {error}</div>}

          <button
            id="auth-submit-btn"
            className="auth-submit"
            type="submit"
            disabled={loading}
          >
            {loading ? '⏳ Please wait…' : tab === 'login' ? '🚀 Sign In' : '✨ Create Account'}
          </button>
        </form>

        <div className="auth-offline-note">
          🔒 <span>100% Offline</span> — No API keys, no internet required
        </div>
      </div>
    </div>
  );
}
