// ─── Pages (thin wrappers that compose components into views) ─────────────────
import React from 'react';
import { RoadmapView } from '../components/Roadmap/RoadmapView';
import { Dashboard }   from '../components/Dashboard/Dashboard';
import { ChatInterface } from '../components/AIMentor/ChatInterface';
import { LeaderboardView } from '../components/Leaderboard/LeaderboardView';
import type { UserProgress } from '../types';

// ── Leaderboard Page ──────────────────────────────────────────────────────────
export const LeaderboardPage: React.FC = () => <LeaderboardView />;

// ── Roadmap Page ──────────────────────────────────────────────────────────────
interface RoadmapPageProps {
  progress: UserProgress | null;
  loading: boolean;
  onSelectLevel: (levelId: number) => void;
  userId: string;
  token: string;
  onProgressUpdate: (updatedProgress: UserProgress) => void;
  isLoggedIn?: boolean;
}
export const RoadmapPage: React.FC<RoadmapPageProps> = ({ progress, loading, onSelectLevel, userId, token, onProgressUpdate, isLoggedIn }) => (
  <RoadmapView
    progress={progress}
    loading={loading}
    onSelectLevel={onSelectLevel}
    userId={userId}
    token={token}
    onProgressUpdate={onProgressUpdate}
    isLoggedIn={isLoggedIn}
  />
);

// ── Dashboard Page ────────────────────────────────────────────────────────────
interface DashboardPageProps {
  progress: UserProgress | null;
  loading: boolean;
  userId: string;
  onProgressUpdate: (updatedProgress: UserProgress) => void;
  token: string;
  onNavigate?: (page: string) => void;
}
export const DashboardPage: React.FC<DashboardPageProps> = ({ progress, loading, userId, onProgressUpdate, token, onNavigate }) => (
  <Dashboard progress={progress} loading={loading} userId={userId} onProgressUpdate={onProgressUpdate} token={token} onNavigate={onNavigate} />
);

// ── Mentor Page ───────────────────────────────────────────────────────────────
interface MentorPageProps { currentLevel?: number; userId: string; }
export const MentorPage: React.FC<MentorPageProps> = ({ currentLevel = 1, userId }) => {
  const LEVEL_TITLES: Record<number, string> = {
    1: 'Level 1 — Distributed Systems Fundamentals',
    2: 'Level 2 — Cryptographic Key & Session Management',
    3: 'Level 3 — System Architecture & Logic Engines',
    4: 'Level 4 — Automated Financial Systems Architecture',
    5: 'Level 5 — Decentralized Governance & Protocol Design',
    6: 'Level 6 — Enterprise FinTech Architecture',
    7: 'Level 7 — High-Throughput Distributed Runtimes',
  };
  return (
    <ChatInterface mentorContext={LEVEL_TITLES[currentLevel] ?? 'General Curriculum'} userId={userId} />
  );
};
