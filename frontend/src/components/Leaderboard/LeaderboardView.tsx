// ─── LeaderboardView — ranked verified on-chain contributors ──────────────────
import React, { useEffect, useState } from 'react';
import { fetchLeaderboard, type LeaderboardRow } from '../../api/client';
import './LeaderboardView.css';

const MEDAL: Record<number, string> = { 1: '🥇', 2: '🥈', 3: '🥉' };

export const LeaderboardView: React.FC = () => {
  const [rows, setRows] = useState<LeaderboardRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [apiError, setApiError] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    setApiError(null);
    fetchLeaderboard()
      .then(setRows)
      .catch((err) => {
        console.error('Error loading leaderboard:', err);
        setApiError(err.message || 'Unable to fetch the leaderboard.');
        setRows([]);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="leaderboard-view">
      <div className="leaderboard-header glass animate-fade-up">
        <div className="leaderboard-header__content">
          <div className="leaderboard-header__badge">🏆 Verified On-Chain Activity</div>
          <h1 className="leaderboard-header__title">
            Developer <span className="gradient-text">Leaderboard</span>
          </h1>
          <p className="leaderboard-header__desc">
            Ranked by distinct verified testnet transactions, then by the number of chains used. Ties go to whoever submitted first.
          </p>
        </div>
      </div>

      <div className="leaderboard-results glass animate-fade-in">
        {loading ? (
          <div className="leaderboard-loading-grid">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="leaderboard-row-skeleton" />
            ))}
          </div>
        ) : apiError ? (
          <div className="leaderboard-empty-state">
            <span className="empty-icon">⚠️</span>
            <h3>Failed to load the leaderboard</h3>
            <p>{apiError}</p>
            <button className="btn btn--primary" onClick={load}>🔄 Retry Connection</button>
          </div>
        ) : rows.length === 0 ? (
          <div className="leaderboard-empty-state">
            <span className="empty-icon">🏁</span>
            <h3>No verified submissions yet</h3>
            <p>Be the first to submit a verified testnet transaction and claim the top spot.</p>
          </div>
        ) : (
          <table className="leaderboard-table">
            <thead>
              <tr>
                <th className="col-rank">Rank</th>
                <th className="col-handle">Telegram</th>
                <th className="col-num">Transactions</th>
                <th className="col-num">Chains</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.telegram} className={row.rank <= 3 ? 'leaderboard-row--top' : ''}>
                  <td className="col-rank">
                    <span className="rank-badge">{MEDAL[row.rank] ?? `#${row.rank}`}</span>
                  </td>
                  <td className="col-handle">@{row.telegram}</td>
                  <td className="col-num">{row.txCount}</td>
                  <td className="col-num">{row.chainCount}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default LeaderboardView;
