// ─── Shared TypeScript types for Developer Academy ────────────────────────────

export interface LevelProgress {
  level_id: number;
  title: string;
  completed_lessons: number;
  total_lessons: number;
  is_unlocked: boolean;
  completed_at: string | null;
}

export interface MentorChatSession {
  session_id: string;
  messages_count: number;
  last_chat_at: string;
  topic?: string;
  summary?: string;
}

export interface UserProgress {
  user_id: string;
  xp: number;
  streak_days: number;
  current_level: number;
  overall_pct: number;
  active_track?: string;
  levels: LevelProgress[];
  last_active: string | null;
  github_username?: string;
  wallet_address?: string;
  github_activities?: GithubActivity[];
  quiz_attempts?: { lesson_id: string; level_id: number; score: number; attempted_at: string }[];
  exercises_submitted?: { lesson_id: string; level_id: number; code: string; submitted_at: string }[];
  hackathons_registered?: string[];
  hackathon_submissions?: Record<string, HackathonSubmission>;
  mentor_chat_sessions?: MentorChatSession[];
  completed_lesson_ids?: string[];
  certificates?: Certificate[];
}

export interface ProgressUpdate {
  level_id: number;
  completed_lessons: number;
  xp_gained: number;
}

export interface TemplateMetadata {
  id: string;
  title: string;
  description: string;
  language: string;
  level_id: number;
  tags: string[];
}

export interface CodeTemplate extends TemplateMetadata {
  code: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  isStreaming?: boolean;
}

export type NavPage = 'academy' | 'roadmap' | 'dashboard' | 'analytics' | 'sandbox' | 'mentor' | 'certificates' | 'forum' | 'hackathons' | 'careers' | 'leaderboard' | 'about' | 'subscriptions';

export interface CompilationResult {
  success: boolean;
  chain: string;
  language: string;
  compiler: string;
  stdout: string;
  stderr?: string;
  syntaxErrors: string[];
  warnings: string[];
  gasEstimate: number;
  artifacts?: {
    abi?: any[];
    bytecode?: string;
    idl?: any;
    programId?: string;
    classHash?: string;
    moduleAddress?: string;
    wasmHash?: string;
    contract_name?: string;
    compiler_target?: string;
  };
}

export interface JobListing {
  id: string;
  title: string;
  company: string;
  location: string;
  remote: boolean;
  salary: string;
  skills: string[];
  url: string;
  date?: string;
  date_epoch?: number;
  is_internship?: boolean;
  is_junior?: boolean;
}

export interface StartupIdea {
  id: number;
  name: string;
  category: string;
  description: string;
  tags: string[];
  icon: string;
}

export interface ForumComment {
  comment_id: string;
  author: string;
  content: string;
  created_at: string;
}

export interface ForumThread {
  thread_id: string;
  title: string;
  author: string;
  category: 'Question' | 'Discussion' | 'Showcase' | 'Help' | 'Announcement';
  content: string;
  tags: string[];
  replies_count: number;
  views_count: number;
  likes_count: number;
  created_at: string;
  comments: ForumComment[];
}

export interface HackathonMilestone {
  title: string;
  date: string;
}

export interface HackathonSubmission {
  project_name: string;
  tagline: string;
  description: string;
  video_link: string;
  code_link: string;
  submitted_at: string;
  is_submitted: boolean;
  team_size: number;
}

export interface Hackathon {
  hackathon_id: string;
  title: string;
  description: string;
  prize_pool: string;
  start_date: string;
  end_date: string;
  status: 'upcoming' | 'ongoing' | 'completed';
  rules: string[];
  tracks: string[];
  milestones: HackathonMilestone[];
  is_registered: boolean;
  submission?: HackathonSubmission;
  ecosystems?: string[];
}

export interface QuizQuestion {
  question: string;
  options: string[];
  correct_idx: number;
}

export interface CodingExercise {
  instruction: string;
  template: string;
  required_keywords: string[];
}

export interface Lesson {
  id: string;
  level_id: number;
  title: string;
  duration: string;
  xp: number;
  content: string;
  quiz: QuizQuestion[];
  exercise?: CodingExercise;
}

export interface Course {
  level_id: number;
  title: string;
  total_lessons: number;
  lessons: Lesson[];
}

export interface Certificate {
  certificate_id: string;
  track_id?: string;
  level_id: number;
  level_title: string;
  issued_at: string;
  recipient: string;
}

export interface GithubActivity {
  commit_sha: string;
  message: string;
  committed_at: string;
}

export interface PlatformKPIs {
  registered_users: number;
  active_learners: number;
  course_completion: number;
  avg_quiz_score: number;
  coding_exercises: number;
  certificates_issued: number;
  github_activity: number;
  ai_mentor_sessions: number;
  deployed_contracts?: number;
}

export interface DashboardData {
  user_progress: UserProgress;
  kpis: PlatformKPIs;
}

export const LEVEL_COLORS: Record<number, string> = {
  1: '#7c3aed',
  2: '#2563eb',
  3: '#0891b2',
  4: '#059669',
  5: '#d97706',
  6: '#dc2626',
  7: '#6366f1',
};

export const LEVEL_ICONS: Record<number, string> = {
  1: '⛓️',
  2: '👛',
  3: '📜',
  4: '💎',
  5: '🏛️',
  6: '🔮',
  7: '🌐',
};
