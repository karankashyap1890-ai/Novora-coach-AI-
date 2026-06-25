import { useState, useEffect } from 'react';
import './Analytics.css';

const API_BASE = 'http://localhost:8000';

const DAY_LABELS = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];

function getShortDay(dateStr) {
  const d = new Date(dateStr + 'T00:00:00');
  return DAY_LABELS[d.getDay()];
}

export default function Analytics({ token, refreshTrigger }) {
  const [summary, setSummary] = useState(null);
  const [trend, setTrend] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!token) return;
    fetchData();
  }, [token, refreshTrigger]);

  async function fetchData() {
    setLoading(true);
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const [sumRes, trendRes] = await Promise.all([
        fetch(`${API_BASE}/analytics/summary`, { headers }),
        fetch(`${API_BASE}/analytics/trend`, { headers }),
      ]);
      if (sumRes.ok) {
        const d = await sumRes.json();
        setSummary(d.analytics || {});
      }
      if (trendRes.ok) {
        const d = await trendRes.json();
        const counts = d.trend?.daily_counts || {};
        const sorted = Object.entries(counts)
          .sort(([a], [b]) => a.localeCompare(b))
          .map(([date, count]) => ({ date, count }));
        setTrend(sorted);
      }
    } catch { /* network error */ }
    finally { setLoading(false); }
  }

  const maxCount = Math.max(...trend.map(t => t.count), 1);
  const today = new Date().toISOString().slice(0, 10);

  if (!token) {
    return (
      <div className="glass-card analytics-panel">
        <div className="analytics-title">📊 Analytics</div>
        <div className="analytics-empty">
          <div className="empty-icon">🔐</div>
          Login to see your productivity stats
        </div>
      </div>
    );
  }

  if (loading && !summary) {
    return (
      <div className="glass-card analytics-panel">
        <div className="analytics-title">📊 Analytics</div>
        <div className="analytics-empty">
          <div className="empty-icon">⏳</div>
          Loading your stats…
        </div>
      </div>
    );
  }

  const noData = !summary || summary.total_sessions === 0;

  return (
    <div className="glass-card analytics-panel">
      <div className="analytics-title">📊 Your Stats</div>

      {noData ? (
        <div className="analytics-empty">
          <div className="empty-icon">🍅</div>
          <p>No sessions yet!<br />Start your first Pomodoro to see your stats here.</p>
        </div>
      ) : (
        <>
          {/* Stat Cards */}
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-value violet">{summary.total_sessions || 0}</div>
              <div className="stat-label">Sessions</div>
            </div>
            <div className="stat-card">
              <div className="stat-value cyan">{summary.total_focus_hours || 0}h</div>
              <div className="stat-label">Focus Time</div>
            </div>
            <div className="stat-card">
              <div className="stat-value amber">{summary.today_sessions || 0}</div>
              <div className="stat-label">Today</div>
            </div>
            <div className="stat-card">
              <div className="stat-value green">
                {summary.avg_focus_score > 0 ? `${summary.avg_focus_score}★` : '—'}
              </div>
              <div className="stat-label">Avg Focus</div>
            </div>
          </div>

          {/* Streak Banner */}
          {summary.streak_days > 0 && (
            <div className="streak-banner">
              <span className="streak-flame">🔥</span>
              <div className="streak-info">
                <div className="streak-count">{summary.streak_days} Day Streak!</div>
                <div className="streak-label">Keep it up — you're building a habit!</div>
              </div>
            </div>
          )}

          {/* Focus Score Bar */}
          {summary.avg_focus_score > 0 && (
            <div className="score-bar-wrap">
              <div className="score-bar-label">
                <span>Average Focus Score</span>
                <span>{summary.avg_focus_score}/5</span>
              </div>
              <div className="score-bar-track">
                <div
                  className="score-bar-fill"
                  style={{ width: `${(summary.avg_focus_score / 5) * 100}%` }}
                />
              </div>
            </div>
          )}

          {/* 7-Day Trend */}
          {trend.length > 0 && (
            <div className="trend-section">
              <div className="trend-title">7-Day Trend</div>
              <div className="trend-bars">
                {trend.map(({ date, count }) => (
                  <div key={date} className="trend-bar-wrap">
                    <div
                      className={`trend-bar ${date === today ? 'today' : ''}`}
                      style={{ height: `${(count / maxCount) * 68}px` }}
                      title={`${date}: ${count} sessions`}
                    />
                    <div className="trend-bar-label">{getShortDay(date)}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
