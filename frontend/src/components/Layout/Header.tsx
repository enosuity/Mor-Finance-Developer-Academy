// ─── Header component with authentication integrations ────────────────────────
import React from 'react';
import type { NavPage, UserProgress } from '../../types';
import './Header.css';

interface HeaderProps {
  activePage: NavPage;
  xp: number;
  streak: number;
  userId: string;
  authType: 'github' | 'wallet' | null;
  progress: UserProgress | null;
  onLoginGitHub: () => void;
  onLoginWallet: () => void;
  onLogout: () => void;
  onLinkGitHub?: () => void;
  onLinkWallet?: () => void;
  onOpenFastTrack?: () => void;
  isMobileNavOpen?: boolean;
  onToggleMobileNav?: () => void;
  isLoggedIn?: boolean;
}

const PAGE_META: Record<NavPage, { title: string; subtitle: string }> = {
  academy:      { title: 'Developer Academy',  subtitle: 'Distributed systems programming & algorithmic design' },
  roadmap:      { title: 'Developer Academy',  subtitle: 'Distributed systems programming & algorithmic design' },
  dashboard:    { title: 'My Dashboard',       subtitle: 'Track your learning progress & software metrics' },
  analytics:    { title: 'Cohort Analytics',   subtitle: 'Ecosystem Developer Cohort Activity (May–August 2026)' },
  sandbox:      { title: 'Multi-Runtime Sandbox', subtitle: 'Universal IDE: Write, compile, and debug system logic engines & distributed software' },
  forum:        { title: 'Community Forum',    subtitle: 'Ask questions, share knowledge, and help others' },
  hackathons:   { title: 'Technical Sprints',  subtitle: 'Build, innovate, and solve real-world challenges' },
  careers:      { title: 'Career Dashboard',   subtitle: 'Software engineering roles, internships & research grants' },
  leaderboard:  { title: 'Leaderboard',        subtitle: 'Top verified on-chain contributors, ranked by testnet activity' },
  mentor:       { title: 'AI Mentor Workspace',subtitle: 'Get real-time code reviews and support' },
  certificates: { title: 'System Credentials', subtitle: 'View and export your verified achievements' },
  subscriptions: { title: 'Subscription Plans', subtitle: 'Choose a subscription plan to unlock premium mentorship and credentials' },
  about:        { title: 'About the Academy',  subtitle: 'Why the Academy exists and how it supports open source' },
};

export const Header: React.FC<HeaderProps> = ({
  activePage,
  xp,
  streak,
  userId,
  authType,
  progress,
  onLoginGitHub,
  onLoginWallet: _onLoginWallet,
  onLogout,
  onLinkGitHub,
  onLinkWallet,
  onOpenFastTrack,
  isMobileNavOpen,
  onToggleMobileNav,
  isLoggedIn = false,
}) => {
  const getHeaderMeta = (page: NavPage, _loggedIn: boolean) => {
    return PAGE_META[page] || { title: 'Academy', subtitle: 'Distributed Systems & Software Engineering' };
  };
  const { title, subtitle } = getHeaderMeta(activePage, isLoggedIn);

  const formatUser = () => {
    if (authType === 'github') {
      return `@${userId.replace('gh-', '')}`;
    }
    if (authType === 'wallet') {
      const addr = userId.replace('wallet-', '');
      if (addr.startsWith('0x') && addr.length === 42) {
        return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
      }
      return addr;
    }
    return 'MOR Builder';
  };

  return (
    <header className="header glass">
      <div className="header__left">
        {onToggleMobileNav && (
          <button
            className={`header__hamburger-btn ${isMobileNavOpen ? 'header__hamburger-btn--active' : ''}`}
            onClick={onToggleMobileNav}
            aria-label="Toggle mobile menu"
            title="Menu"
          >
            <span />
            <span />
            <span />
          </button>
        )}
        <div className="header__title-group">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <img src="/mor-logo.png" alt="MOR Developer Academy" style={{ width: '22px', height: '22px', objectFit: 'contain', filter: 'drop-shadow(0 0 6px rgba(59,130,246,0.6))' }} />
            <h1 className="header__title">{title}</h1>
          </div>
          <p className="header__subtitle">{subtitle}</p>
        </div>
      </div>
      <div className="header__right">
        {/* External Community & Resource Links */}
        <div className="header__links">
          <a
            href="https://github.com/Mor-Fin-AI"
            target="_blank"
            rel="noopener noreferrer"
            className="header__icon-btn"
            title="MOR Developer Academy GitHub Org"
          >
            <span>🐙</span>
            <span className="header__link-label">GitHub</span>
          </a>
          <a
            href="https://discord.gg/Jjt52cQEV"
            target="_blank"
            rel="noopener noreferrer"
            className="header__icon-btn header__discord-btn"
            title="Developer Community Discord"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
              <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515a.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0a12.64 12.64 0 0 0-.617-1.25a.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057a19.9 19.9 0 0 0 5.993 3.03a.078.078 0 0 0 .084-.028a14.09 14.09 0 0 0 1.226-1.994a.076.076 0 0 0-.041-.106a13.107 13.107 0 0 1-1.872-.892a.077.077 0 0 1-.008-.128a10.2 10.2 0 0 0 .372-.292a.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.061 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127a12.299 12.299 0 0 1-1.873.892a.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028a19.839 19.839 0 0 0 6.002-3.03a.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.028zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.956-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.955-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.946 2.418-2.157 2.418z"/>
            </svg>
            <span className="header__link-label">Discord</span>
          </a>
        </div>

        {/* Fast Track Institutional Enrollment Button */}
        {onOpenFastTrack && (
          <button
            className="header__fast-track-btn"
            onClick={onOpenFastTrack}
            title="Kenyatta University Fast Track Enrollment"
          >
            <span className="header__fast-track-text-full">🎓 Fast Track (KU)</span>
            <span className="header__fast-track-text-mobile">🎓 KU Fast Track</span>
            <span className="header__fast-track-text-compact">🎓 KU</span>
          </button>
        )}

        {/* Auth section */}
        <div className="header__auth">
          {authType ? (
            <div className="auth-profile">
              <span className="auth-profile__icon">{authType === 'github' ? '🐱' : '🔑'}</span>
              <span className="auth-profile__name" title={userId}>{formatUser()}</span>
              {authType === 'wallet' && !progress?.github_username && (
                <button className="btn btn--secondary btn--xs header-link-btn" onClick={onLinkGitHub} title="Link GitHub account" style={{ fontSize: '0.7rem', padding: '3px 8px', marginLeft: 8 }}>
                  🐱 Link GitHub
                </button>
              )}
              {authType === 'github' && !progress?.wallet_address && (
                <button className="btn btn--secondary btn--xs header-link-btn" onClick={onLinkWallet} title="Link Developer Credential" style={{ fontSize: '0.7rem', padding: '3px 8px', marginLeft: 8 }}>
                  🔑 Link Developer Key
                </button>
              )}
              <button className="auth-profile__logout" onClick={onLogout} title="Disconnect session">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                  <polyline points="16 17 21 12 16 7"></polyline>
                  <line x1="21" y1="12" x2="9" y2="12"></line>
                </svg>
              </button>
            </div>
          ) : (
            <div className="auth-buttons">
              <button className="btn btn--primary btn--sm" onClick={onLoginGitHub}>
                🐱 Student Login
              </button>
            </div>
          )}
        </div>

        {/* Stats */}
        <div className="header__stat" title="Current streak">
          <span className="header__stat-icon">🔥</span>
          <span className="header__stat-value">{streak}</span>
          <span className="header__stat-label">day streak</span>
        </div>
        <div className="header__stat header__stat--xp" title="Total XP">
          <span className="header__stat-icon">⚡</span>
          <span className="header__stat-value">{xp.toLocaleString()}</span>
          <span className="header__stat-label">XP</span>
        </div>
      </div>
    </header>
  );
};

export default Header;
