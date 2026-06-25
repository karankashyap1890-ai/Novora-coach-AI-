import { useState, useEffect, useCallback, useRef } from 'react';
import './Timer.css';

const STATE_LABELS = {
  idle:        'Ready',
  work:        'Focus Time',
  short_break: 'Short Break',
  long_break:  'Long Break 🎉',
  paused:      'Paused',
  completed:   'Complete',
};

const RADIUS = 116;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

export default function PomodoroTimer({ onSessionStart, onSessionComplete, onStatusUpdate }) {
  const [timerState, setTimerState] = useState({
    state: 'idle',
    remaining_seconds: 25 * 60,
    session_number: 0,
    task_title: '',
    work_minutes: 25,
    completed_sessions: 0,
    is_active: false,
  });
  const [taskInput, setTaskInput] = useState('');
  const intervalRef = useRef(null);
  const totalSecondsRef = useRef(25 * 60);

  // Tick the local timer every second
  useEffect(() => {
    if (timerState.is_active && timerState.state !== 'paused') {
      intervalRef.current = setInterval(() => {
        setTimerState(prev => {
          const next = prev.remaining_seconds - 1;
          if (next <= 0) {
            clearInterval(intervalRef.current);
            handleTimerComplete(prev);
            return { ...prev, remaining_seconds: 0 };
          }
          onStatusUpdate?.({ ...prev, remaining_seconds: next });
          return { ...prev, remaining_seconds: next };
        });
      }, 1000);
    } else {
      clearInterval(intervalRef.current);
    }
    return () => clearInterval(intervalRef.current);
  }, [timerState.is_active, timerState.state]);

  const handleTimerComplete = (prev) => {
    if (prev.state === 'work') {
      const breakSecs = prev.session_number % 4 === 0 ? 15 * 60 : 5 * 60;
      const newState = prev.session_number % 4 === 0 ? 'long_break' : 'short_break';
      totalSecondsRef.current = breakSecs;
      setTimerState(s => ({
        ...s,
        state: newState,
        remaining_seconds: breakSecs,
        completed_sessions: s.completed_sessions + 1,
        is_active: true,
      }));
      onSessionComplete?.(prev);
    } else {
      setTimerState(s => ({ ...s, state: 'idle', remaining_seconds: 25 * 60, is_active: false }));
    }
  };

  const handleStart = useCallback(() => {
    if (!taskInput.trim()) return;
    totalSecondsRef.current = timerState.work_minutes * 60;
    const newState = {
      state: 'work',
      remaining_seconds: timerState.work_minutes * 60,
      session_number: timerState.session_number + 1,
      task_title: taskInput.trim(),
      work_minutes: timerState.work_minutes,
      completed_sessions: timerState.completed_sessions,
      is_active: true,
    };
    setTimerState(newState);
    onSessionStart?.(newState);
  }, [taskInput, timerState]);

  const handlePause = useCallback(() => {
    if (timerState.state === 'paused') {
      setTimerState(prev => ({ ...prev, state: 'work', is_active: true }));
    } else {
      setTimerState(prev => ({ ...prev, state: 'paused', is_active: false }));
    }
  }, [timerState.state]);

  const handleReset = useCallback(() => {
    clearInterval(intervalRef.current);
    setTimerState(prev => ({
      ...prev,
      state: 'idle',
      remaining_seconds: prev.work_minutes * 60,
      is_active: false,
    }));
  }, []);

  // SVG progress calculation
  const totalSecs = timerState.state === 'work'
    ? timerState.work_minutes * 60
    : timerState.state === 'short_break' ? 5 * 60
    : timerState.state === 'long_break' ? 15 * 60
    : totalSecondsRef.current;

  const progress = totalSecs > 0 ? timerState.remaining_seconds / totalSecs : 1;
  const dashOffset = CIRCUMFERENCE * (1 - progress);
  const mins = Math.floor(timerState.remaining_seconds / 60);
  const secs = timerState.remaining_seconds % 60;

  const isIdle = timerState.state === 'idle';
  const isPaused = timerState.state === 'paused';
  const isActive = timerState.is_active;

  // Dot indicators (4 session cycle)
  const dots = Array.from({ length: 4 }, (_, i) => {
    const sessionsInCycle = timerState.completed_sessions % 4;
    if (i < sessionsInCycle) return 'completed';
    if (i === sessionsInCycle && timerState.state === 'work') return 'current';
    return 'empty';
  });

  return (
    <div className="glass-card timer-panel">
      {/* SVG Defs */}
      <svg width="0" height="0" style={{ position: 'absolute' }}>
        <defs>
          <linearGradient id="violetGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#9d5ff3" />
            <stop offset="100%" stopColor="#7c3aed" />
          </linearGradient>
          <linearGradient id="cyanGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#22d3ee" />
            <stop offset="100%" stopColor="#06b6d4" />
          </linearGradient>
          <linearGradient id="greenGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#34d399" />
            <stop offset="100%" stopColor="#10b981" />
          </linearGradient>
        </defs>
      </svg>

      {/* Timer Ring */}
      <div className={`timer-ring-container ${isActive ? 'is-active' : ''} state-${timerState.state}`}>
        <svg className="timer-svg" viewBox="0 0 260 260">
          <circle
            className="timer-ring-bg"
            cx="130" cy="130" r={RADIUS}
          />
          <circle
            className={`timer-ring-progress state-${timerState.state}`}
            cx="130" cy="130" r={RADIUS}
            strokeDasharray={CIRCUMFERENCE}
            strokeDashoffset={dashOffset}
          />
        </svg>

        <div className="timer-center">
          <span className="timer-state-label">{STATE_LABELS[timerState.state]}</span>
          <div className={`timer-display state-${timerState.state}`}>
            {String(mins).padStart(2, '0')}:{String(secs).padStart(2, '0')}
          </div>
          <span className="timer-session-badge">
            Session #{timerState.session_number || '—'}
          </span>
        </div>
      </div>

      {/* Task Title */}
      {timerState.task_title && (
        <div className="timer-task-info">
          <div className="timer-task-label">Current Task</div>
          <div className="timer-task-title">{timerState.task_title}</div>
        </div>
      )}

      {/* Task Input (when idle) */}
      {isIdle && (
        <div className="task-input-bar animate-fade-in">
          <input
            id="task-input"
            className="input"
            placeholder="What are you working on? 🎯"
            value={taskInput}
            onChange={e => setTaskInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleStart()}
            maxLength={200}
            autoFocus
          />
        </div>
      )}

      {/* Controls */}
      <div className="timer-controls">
        {isIdle ? (
          <button
            id="btn-start-timer"
            className="timer-btn-main play"
            onClick={handleStart}
            disabled={!taskInput.trim()}
            title="Start session"
          >▶</button>
        ) : (
          <>
            <button
              id="btn-secondary-left"
              className="timer-btn-secondary"
              onClick={handleReset}
              title="Reset"
            >↺</button>
            <button
              id="btn-pause-timer"
              className={`timer-btn-main ${isPaused ? 'play' : 'pause'}`}
              onClick={handlePause}
              title={isPaused ? 'Resume' : 'Pause'}
            >
              {isPaused ? '▶' : '⏸'}
            </button>
            <button
              id="btn-secondary-right"
              className="timer-btn-secondary"
              onClick={() => handleTimerComplete(timerState)}
              title="Skip to break"
            >⏭</button>
          </>
        )}
      </div>

      {/* Session Dots */}
      <div className="session-dots" aria-label="Session progress">
        {dots.map((type, i) => (
          <div key={i} className={`session-dot ${type}`} title={`Session ${i + 1}`} />
        ))}
        <span className="timer-session-badge" style={{ marginLeft: 4 }}>
          {timerState.completed_sessions} done
        </span>
      </div>
    </div>
  );
}
