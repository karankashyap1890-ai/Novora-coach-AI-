import { useState, useEffect, useRef, useCallback } from 'react';
import './ChatPanel.css';

const API_BASE = 'http://localhost:8000';

const QUICK_ACTIONS = [
  { label: '▶ Start session', text: 'Start! I want to focus' },
  { label: '⏸ Pause', text: 'Pause' },
  { label: '📊 Status', text: 'What is my status?' },
  { label: '📈 Stats', text: 'Show my stats' },
  { label: '❓ Help', text: 'Help' },
];

const WELCOME_MESSAGE = {
  id: 'welcome',
  role: 'assistant',
  content: `👋 Hello! I'm **Coach Novora** — your personal Pomodoro productivity coach! 🍅

I'll guide you through focused 25-minute work sessions followed by refreshing breaks.

**To get started, tell me:**
*What are you working on today?*

You can say things like:
• *"Start — writing my project report"*
• *"Focus on studying Python"*
• *"Help"* — to see all commands`,
  timestamp: new Date().toISOString(),
};

function formatTime(iso) {
  try {
    return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch { return ''; }
}

function MessageBubble({ msg, isStreaming }) {
  const isAgent = msg.role === 'assistant';
  return (
    <div className={`message ${isAgent ? 'agent-message' : 'user-message'}`}>
      <div className="message-avatar">
        {isAgent ? '🍅' : '👤'}
      </div>
      <div className="message-content">
        <div className="message-bubble">
          {msg.content}
          {isStreaming && <span className="streaming-cursor" />}
        </div>
        <div className="message-time">{formatTime(msg.timestamp)}</div>
      </div>
    </div>
  );
}

export default function ChatPanel({ token, timerState, onTimerCommand }) {
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [streamingId, setStreamingId] = useState(null);
  const messagesEndRef = useRef(null);
  const wsRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => { scrollToBottom(); }, [messages, isTyping]);

  // WebSocket connection
  useEffect(() => {
    if (!token) return;
    const userId = getUserIdFromToken(token);
    connectWebSocket(userId);
    return () => wsRef.current?.close();
  }, [token]);

  // Timer event → auto-message
  useEffect(() => {
    if (timerState?.event === 'session_complete') {
      addAgentMessage(
        `🎉 Your Pomodoro session is done! Great work!\n\n` +
        `Please rate your focus:\n⭐ **1–5** — How focused were you? Just reply with a number and any thoughts!`
      );
    } else if (timerState?.event === 'break_done') {
      addAgentMessage(`☀️ Break's over! Ready to start the next session? Tell me what you're working on! 🚀`);
    }
  }, [timerState?.event]);

  function getUserIdFromToken(tok) {
    try {
      const payload = JSON.parse(atob(tok.split('.')[1]));
      return payload.sub || 'user';
    } catch { return 'user'; }
  }

  function connectWebSocket(userId) {
    const ws = new WebSocket(`ws://localhost:8000/chat/ws/${userId}`);
    wsRef.current = ws;

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => {
      setIsConnected(false);
      // Reconnect after 3 seconds
      setTimeout(() => userId && connectWebSocket(userId), 3000);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleWsMessage(data);
      } catch { /* ignore malformed */ }
    };
  }

  function handleWsMessage(data) {
    switch (data.type) {
      case 'agent_message':
        setIsTyping(false);
        addAgentMessage(data.content);
        break;
      case 'agent_stream': {
        setIsTyping(false);
        setStreamingId(id => {
          const sid = id || `stream-${Date.now()}`;
          setMessages(prev => {
            const existing = prev.find(m => m.id === sid);
            if (existing) {
              return prev.map(m => m.id === sid
                ? { ...m, content: data.content }
                : m
              );
            }
            return [...prev, {
              id: sid,
              role: 'assistant',
              content: data.content,
              timestamp: new Date().toISOString(),
            }];
          });
          if (data.done) setStreamingId(null);
          return data.done ? null : sid;
        });
        break;
      }
      case 'typing':
        setIsTyping(true);
        break;
      case 'timer_event':
        onTimerCommand?.(data);
        break;
      default:
        break;
    }
  }

  function addAgentMessage(content) {
    setMessages(prev => [...prev, {
      id: `agent-${Date.now()}`,
      role: 'assistant',
      content,
      timestamp: new Date().toISOString(),
    }]);
  }

  const sendMessage = useCallback(async (text) => {
    const trimmed = text.trim();
    if (!trimmed || !token) return;

    // Add user message
    setMessages(prev => [...prev, {
      id: `user-${Date.now()}`,
      role: 'user',
      content: trimmed,
      timestamp: new Date().toISOString(),
    }]);
    setInputText('');

    // Try WebSocket first, fall back to REST
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ message: trimmed }));
    } else {
      // REST fallback
      setIsTyping(true);
      try {
        const res = await fetch(`${API_BASE}/chat/message`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({ message: trimmed }),
        });
        const data = await res.json();
        setIsTyping(false);
        if (data.agent_message) {
          addAgentMessage(data.agent_message.content);
        }
      } catch {
        setIsTyping(false);
        addAgentMessage('⚠️ Connection issue. Please make sure the backend is running.');
      }
    }
  }, [token]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(inputText);
    }
  };

  return (
    <div className="glass-card chat-panel">
      {/* Header */}
      <div className="chat-header">
        <div className="chat-avatar">🍅</div>
        <div className="chat-header-info">
          <div className="chat-header-name">Coach Novora</div>
          <div className="chat-header-status">
            {isConnected ? 'Online — Offline AI' : 'Connecting…'}
          </div>
        </div>
        <span className="badge badge-violet">Offline AI</span>
      </div>

      {/* Messages */}
      <div className="chat-messages" role="log" aria-live="polite">
        {messages.map(msg => (
          <MessageBubble
            key={msg.id}
            msg={msg}
            isStreaming={msg.id === streamingId}
          />
        ))}
        {isTyping && (
          <div className="typing-indicator">
            <div className="message-avatar" style={{ background: 'linear-gradient(135deg, #7c3aed, #5b21b6)', borderRadius: '50%', width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>🍅</div>
            <div className="typing-dots">
              <div className="typing-dot" />
              <div className="typing-dot" />
              <div className="typing-dot" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Action Chips */}
      <div className="chat-quick-actions">
        {QUICK_ACTIONS.map(({ label, text }) => (
          <button
            key={label}
            className="quick-action-chip"
            onClick={() => sendMessage(text)}
            type="button"
          >
            {label}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="chat-input-bar">
        <textarea
          id="chat-input"
          ref={inputRef}
          className="chat-input"
          placeholder="Talk to Coach Novora… (Enter to send)"
          value={inputText}
          onChange={e => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          maxLength={2000}
          disabled={!token}
        />
        <button
          id="chat-send-btn"
          className="chat-send-btn"
          onClick={() => sendMessage(inputText)}
          disabled={!inputText.trim() || !token}
          aria-label="Send message"
        >
          ➤
        </button>
      </div>
    </div>
  );
}
