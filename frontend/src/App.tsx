// ─── App — root component with state, layout, authentication and routing ───
import { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import type { NavPage, UserProgress, Course } from './types';
import { fetchProgress, fetchCourses, authGithub, authWallet, fetchAuthConfig, enrollUniversityStudent } from './api/client';
import { Sidebar } from './components/Layout/Sidebar';
import { Header }  from './components/Layout/Header';
import { HeadLayoutMeta } from './components/Layout/HeadLayoutMeta';
import { RoadmapPage, DashboardPage, MentorPage, LeaderboardPage } from './pages';
import { LessonsList } from './components/Roadmap/LessonsList';
import { LessonView } from './components/Roadmap/LessonView';
import { CertificatesView } from './components/Certificates/CertificatesView';
import { ForumView } from './components/Forum/ForumView';
import { HackathonsView } from './components/Hackathons/HackathonsView';
import { LandingPage } from './components/Auth/LandingPage';
import { AboutPage } from './components/About/AboutPage';
import { SubscriptionPlans } from './components/Subscriptions/SubscriptionPlans';
import { CareerDashboard } from './components/Careers/CareerDashboard';
import { PlaygroundView } from './components/Sandbox/PlaygroundView';
import { FastTrackEnrollmentModal } from './components/Auth/FastTrackEnrollmentModal';
import './index.css';

export default function App() {
  const location = useLocation();
  const navigate = useNavigate();

  const getActivePage = (): NavPage => {
    const path = location.pathname;
    if (path.startsWith('/academy') || path.startsWith('/roadmap')) return 'academy';
    if (path.startsWith('/dashboard')) return 'dashboard';
    if (path.startsWith('/analytics')) return 'analytics';
    if (path.startsWith('/sandbox') || path.startsWith('/playground')) return 'sandbox';
    if (path.startsWith('/forum')) return 'forum';
    if (path.startsWith('/hackathons')) return 'hackathons';
    if (path.startsWith('/careers')) return 'careers';
    if (path.startsWith('/leaderboard')) return 'leaderboard';
    if (path.startsWith('/mentor')) return 'mentor';
    if (path.startsWith('/certificates')) return 'certificates';
    if (path.startsWith('/subscriptions')) return 'subscriptions';
    if (path.startsWith('/about')) return 'about';
    return 'academy';
  };
  const activePage = getActivePage();
  
  // Helpers to read/write session cookie
  const getSessionCookie = () => {
    const name = "user_session=";
    const decodedCookie = decodeURIComponent(document.cookie);
    const ca = decodedCookie.split(';');
    for (let i = 0; i < ca.length; i++) {
      let c = ca[i].trim();
      if (c.indexOf(name) === 0) {
        try {
          return JSON.parse(c.substring(name.length, c.length));
        } catch (e) {
          return null;
        }
      }
    }
    return null;
  };

  const setSessionCookie = (uid: string, type: 'github' | 'wallet' | 'demo', token: string) => {
    document.cookie = `user_session=${JSON.stringify({ userId: uid, authType: type, token })}; path=/; max-age=86400; SameSite=Lax`;
  };

  const deleteSessionCookie = () => {
    document.cookie = "user_session=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC; SameSite=Lax";
  };

  // Initialize state from cookie if present
  const initialSession = getSessionCookie();

  // Auth state
  const [userId, setUserId] = useState<string>(initialSession?.userId || '');
  const [authType, setAuthType] = useState<'github' | 'wallet' | null>(initialSession?.authType || null);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [jwtToken, setJwtToken] = useState<string | null>(initialSession?.token || null);
  
  // Progress & curriculum states
  const [progress, setProgress] = useState<UserProgress | null>(null);
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Roadmap Drilldown states
  const [selectedLevel, setSelectedLevel] = useState<number | null>(null);
  const [selectedLessonId, setSelectedLessonId] = useState<string | null>(null);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [showFastTrackModal, setShowFastTrackModal] = useState(false);
  const [enrollCohort, setEnrollCohort] = useState('KU_COHORT_2026_01');
  const [enrollUniversity, setEnrollUniversity] = useState('Kenyatta University');
  const [enrollRedirecting, setEnrollRedirecting] = useState(false);

  // Check for direct enrollment link (e.g. /enroll, ?cohort=..., or ?enroll=true)
  // Automatically routes user directly to GitHub OAuth authorization without intermediate modal click
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    // If returning from GitHub OAuth with an authorization callback code, let the code handler below process it!
    if (code) return;

    const cohort = params.get('cohort');
    const univ = params.get('university');
    const isEnrollPath = window.location.pathname.startsWith('/enroll');
    const isEnrollQuery = params.get('enroll') === 'true' || Boolean(cohort);

    if (cohort || isEnrollPath || isEnrollQuery) {
      const targetCohort = cohort || 'KU_COHORT_2026_01';
      const targetUniv = univ || 'Kenyatta University';
      setEnrollCohort(targetCohort);
      setEnrollUniversity(targetUniv);

      const session = getSessionCookie();
      if (session?.userId) {
        navigate('/sandbox');
        return;
      }

      // Automatically launch frictionless GitHub OAuth redirection directly
      setEnrollRedirecting(true);
      setLoading(true);
      import('./api/client').then(({ initiateFrictionlessEnrollment }) => {
        initiateFrictionlessEnrollment(
          undefined,
          window.location.origin,
          targetUniv,
          targetCohort,
          5000
        ).catch((err) => {
          console.error("Direct enrollment auto-redirection error, falling back to modal:", err);
          setEnrollRedirecting(false);
          setLoading(false);
          setLoginError(err.message || "Automatic GitHub redirection failed. Please use the button below.");
          setShowFastTrackModal(true);
        });
      });
    }
  }, [location.pathname]);

  // Check for GitHub OAuth callback code in URL on mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const stateParam = params.get('state');

    if (code) {
      // Clear URL params immediately to avoid re-triggering exchange
      window.history.replaceState({}, document.title, window.location.pathname);
      
      setLoading(true);
      const session = getSessionCookie();
      if (session && session.authType === 'wallet') {
        // Link GitHub to active wallet user session
        import('./api/client').then(({ linkGithub }) => {
          linkGithub(session.userId, code)
            .then((resProgress) => {
              setUserId(resProgress.user_id);
              setAuthType(session.authType);
              setSessionCookie(resProgress.user_id, session.authType, session.token || jwtToken || '');
              setProgress(resProgress);
              alert("GitHub account linked successfully to your developer profile!");
            })
            .catch((err) => {
              console.error("Link GitHub error:", err);
              alert(err.message || "Failed to link GitHub to developer profile.");
            })
            .finally(() => setLoading(false));
        });
      } else {
        // Parse university / cohort metadata from state if present
        let university = 'Kenyatta University';
        let cohort = 'KU_COHORT_2026_01';
        if (stateParam) {
          try {
            const parsed = JSON.parse(atob(stateParam));
            if (parsed.university) university = parsed.university;
            if (parsed.cohort) cohort = parsed.cohort;
          } catch (e) {
            console.warn("Could not decode OAuth state param:", e);
          }
        }

        // Fast-Track University Enrollment Callback Flow with timeout safeguard
        const oauthCallbackTimer = setTimeout(() => {
          setLoading(false);
          alert("GitHub authentication verification timed out (12s). Please retry logging in.");
        }, 12000);

        enrollUniversityStudent({
          oauth_code: code,
          university_affiliate: university,
          cohort_id: cohort
        })
          .then(({ token, user, unlocked_sandbox }) => {
            clearTimeout(oauthCallbackTimer);
            const uid = user.user_id || user._id;
            setUserId(uid);
            setAuthType('github');
            setJwtToken(token);
            setSessionCookie(uid, 'github', token);
            setProgress(user);
            setSelectedLevel(null);
            setSelectedLessonId(null);
            if (unlocked_sandbox) {
              navigate('/sandbox');
            } else {
              navigate('/academy');
            }
          })
          .catch((err) => {
            console.warn("Fast-track callback fallback to standard auth:", err);
            authGithub(undefined, code)
              .then(({ token, user }) => {
                clearTimeout(oauthCallbackTimer);
                setUserId(user.user_id);
                setAuthType('github');
                setJwtToken(token);
                setSessionCookie(user.user_id, 'github', token);
                setProgress(user);
                setSelectedLevel(null);
                setSelectedLessonId(null);
                navigate('/academy');
              })
              .catch((stdErr) => {
                clearTimeout(oauthCallbackTimer);
                console.error("GitHub OAuth callback error:", stdErr);
                alert("GitHub OAuth authentication failed. Please verify network connectivity and GitHub OAuth credentials.");
              });
          })
          .finally(() => setLoading(false));
      }
    }
  }, []);

  // Load curriculum metadata reactively when user active track changes
  useEffect(() => {
    const track = progress?.active_track || 'ethereum';
    fetchCourses(track)
      .then(setCourses)
      .catch((err) => console.error("Error fetching courses:", err));
  }, [progress?.active_track]);

  // Fetch progress reactively when user identity changes
  useEffect(() => {
    if (!userId) {
      setProgress(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    fetchProgress(userId)
      .then(setProgress)
      .catch((err) => {
        console.error("Error fetching user progress:", err);
        setProgress(null);
      })
      .finally(() => setLoading(false));
  }, [userId]);

  const handleLoginGitHub = async () => {
    try {
      setLoginError(null);
      setLoading(true);

      const timeoutTimer = setTimeout(() => {
        setLoading(false);
        setLoginError('GitHub authorization initialization timed out (8s). Please try again.');
      }, 8000);

      let clientId = (import.meta as any).env?.VITE_GITHUB_CLIENT_ID;
      let redirectUri = (import.meta as any).env?.VITE_GITHUB_REDIRECT_URI || window.location.origin;

      try {
        const config = await fetchAuthConfig(4000);
        if (config.github_client_id && config.github_client_id.trim() && config.github_client_id !== 'YOUR_GITHUB_CLIENT_ID_CONFIG') {
          clientId = config.github_client_id.trim();
          redirectUri = config.github_redirect_uri || redirectUri;
        }
      } catch (err) {
        console.warn("Could not retrieve backend auth config within timeout, using fallback client ID:", err);
      }

      if (!clientId || clientId === 'YOUR_GITHUB_CLIENT_ID_CONFIG') {
        clientId = 'Ov23liJ2hxzWckVzJpxM';
      }

      clearTimeout(timeoutTimer);
      const redirectUrl = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=user:email`;
      window.location.href = redirectUrl;
      return;
    } catch (err: any) {
      console.warn("GitHub OAuth initialization error:", err);
      setLoginError(err.message || "Failed to initialize GitHub OAuth.");
    } finally {
      setLoading(false);
    }

    // Fallback Mock Login if Client ID is not configured
    const username = prompt("Enter your GitHub username to connect (Fallback Mock Mode):");
    if (!username || !username.trim()) return;

    try {
      setLoading(true);
      const { token, user } = await authGithub(username.trim());
      setUserId(user.user_id);
      setAuthType('github');
      setJwtToken(token);
      setSessionCookie(user.user_id, 'github', token);
      setProgress(user);
      setSelectedLevel(null);
      setSelectedLessonId(null);
      navigate('/academy');
    } catch (err) {
      console.error(err);
      alert("Failed to authenticate with GitHub.");
    } finally {
      setLoading(false);
    }
  };

  const handleLoginWallet = async () => {
    setLoginError(null);
    const win = window as any;
    if (win.ethereum) {
      try {
        setLoading(true);
        // 1. Request Account Access
        const accounts = await win.ethereum.request({ method: 'eth_requestAccounts' });
        const address = accounts[0];
        
        // 2. Generate Authentication Message with Nonce
        const message = `Welcome to Developer Academy!\n\nSign this message to authenticate your developer session.\nNonce: ${Math.floor(Math.random() * 1000000)}`;
        
        // 3. Request Cryptographic Signature
        const signature = await win.ethereum.request({
          method: 'personal_sign',
          params: [message, address],
        });
        
        // 4. Submit to Backend for Cryptographic Verification
        const { token, user } = await authWallet(address, message, signature);
        setUserId(user.user_id);
        setAuthType('wallet');
        setJwtToken(token);
        setSessionCookie(user.user_id, 'wallet', token);
        setProgress(user);
        setSelectedLevel(null);
        setSelectedLessonId(null);
        navigate('/academy');
        return;
      } catch (err: any) {
        console.error("Developer key signature auth failed:", err);
        setLoginError(err.message || "Failed to authenticate developer key.");
        return;
      } finally {
        setLoading(false);
      }
    }

    // Fallback Mock Login if no cryptographic key provider is present or if user cancels signature
    const address = prompt(
      "Enter your Authorized Developer Key Address (PKI / 0x...):",
      "0x" + Array.from({ length: 40 }, () => Math.floor(Math.random() * 16).toString(16)).join("")
    );
    if (!address || !address.trim() || !address.startsWith("0x") || address.length !== 42) {
      alert("Invalid Developer Key address format.");
      return;
    }

    try {
      setLoading(true);
      const { token, user } = await authWallet(address.trim());
      setUserId(user.user_id);
      setAuthType('wallet');
      setJwtToken(token);
      setSessionCookie(user.user_id, 'wallet', token);
      setProgress(user);
      setSelectedLevel(null);
      setSelectedLessonId(null);
      navigate('/academy');
    } catch (err: any) {
      console.error(err);
      setLoginError(err.message || "Failed to authenticate developer key.");
    } finally {
      setLoading(false);
    }
  };

  const handleLinkGitHub = async () => {
    try {
      setLoading(true);

      const timeoutTimer = setTimeout(() => {
        setLoading(false);
        alert("GitHub linking request timed out (8s).");
      }, 8000);

      let clientId = (import.meta as any).env?.VITE_GITHUB_CLIENT_ID;
      let redirectUri = (import.meta as any).env?.VITE_GITHUB_REDIRECT_URI || window.location.origin;

      try {
        const config = await fetchAuthConfig(4000);
        if (config.github_client_id && config.github_client_id.trim() && config.github_client_id !== 'YOUR_GITHUB_CLIENT_ID_CONFIG') {
          clientId = config.github_client_id.trim();
          redirectUri = config.github_redirect_uri || redirectUri;
        }
      } catch (err) {
        console.warn("Could not retrieve public auth config, using fallback ID:", err);
      }

      if (!clientId || clientId === 'YOUR_GITHUB_CLIENT_ID_CONFIG') {
        clientId = 'Ov23liJ2hxzWckVzJpxM';
      }

      clearTimeout(timeoutTimer);
      const redirectUrl = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=user`;
      window.location.href = redirectUrl;
      return;
    } catch (err) {
      console.warn("Could not retrieve auth config for linking:", err);
    } finally {
      setLoading(false);
    }

    const username = prompt("Enter your GitHub username to link (Fallback Mock Mode):");
    if (!username || !username.trim()) return;

    try {
      setLoading(true);
      const { linkGithub } = await import('./api/client');
      const resProgress = await linkGithub(userId, undefined, username.trim());
      setProgress(resProgress);
      alert(`GitHub account @${username.trim()} linked successfully!`);
    } catch (err: any) {
      console.error(err);
      alert(err.message || "Failed to link GitHub to developer profile.");
    } finally {
      setLoading(false);
    }
  };

  const handleLinkWallet = async () => {
    const win = window as any;
    let address = "";
    let signature = "mock_signature";
    let message = `Link Developer Key to Developer Academy`;

    if (win.ethereum) {
      try {
        setLoading(true);
        const accounts = await win.ethereum.request({ method: 'eth_requestAccounts' });
        address = accounts[0];
        message = `Welcome to Developer Academy!\n\nSign this message to link this Developer Key to your profile.\nNonce: ${Math.floor(Math.random() * 1000000)}`;
        signature = await win.ethereum.request({
          method: 'personal_sign',
          params: [message, address],
        });
      } catch (err) {
        console.error("Link Developer Key signature failed, attempting mock link:", err);
      } finally {
        setLoading(false);
      }
    }

    if (!address) {
      const input = prompt(
        "Enter Developer Key Address to link (Fallback Mock Mode):",
        "0x" + Array.from({ length: 40 }, () => Math.floor(Math.random() * 16).toString(16)).join("")
      );
      if (!input || !input.trim() || !input.startsWith("0x") || input.length !== 42) {
        alert("Invalid Developer Key address format.");
        return;
      }
      address = input.trim();
    }

    try {
      setLoading(true);
      const { linkWallet } = await import('./api/client');
      const resProgress = await linkWallet(userId, address, message, signature);
      setProgress(resProgress);
      alert(`Developer Key ${address} linked successfully!`);
    } catch (err: any) {
      console.error(err);
      alert(err.message || "Failed to link Developer Key to GitHub profile.");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    deleteSessionCookie();
    setUserId('');
    setAuthType(null);
    setJwtToken(null);
    setSelectedLevel(null);
    setSelectedLessonId(null);
    navigate('/login');
  };

  const handleProgressUpdate = (updatedProgress: UserProgress) => {
    setProgress(updatedProgress);
  };

  const handleNavigate = (page: NavPage) => {
    // Reset drilldowns when navigating to top-level pages
    setSelectedLevel(null);
    setSelectedLessonId(null);
    navigate(page === 'academy' ? '/academy' : `/${page}`);
  };

  const isLoggedIn = Boolean(authType && userId);

  // If unauthenticated and on the root or login route, show the full LandingPage
  if (!isLoggedIn && (location.pathname === '/' || location.pathname === '/login')) {
    return (
      <>
        <HeadLayoutMeta isLoggedIn={false} />
        {enrollRedirecting && (
          <div
            style={{
              position: 'fixed',
              inset: 0,
              backgroundColor: 'rgba(3, 3, 7, 0.94)',
              backdropFilter: 'blur(20px)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 10000,
              color: '#fff',
              textAlign: 'center',
              padding: '24px',
            }}
          >
            <div className="spinner" style={{ width: '48px', height: '48px', borderWidth: '4px', marginBottom: '24px' }} />
            <h3 style={{ fontSize: '1.45rem', fontWeight: 800, marginBottom: '10px' }}>
              Routing to GitHub Authorization...
            </h3>
            <p style={{ fontSize: '0.95rem', color: '#94a3b8', maxWidth: '440px', lineHeight: 1.6 }}>
              Fast-tracking your enrollment for <strong>{enrollUniversity}</strong> ({enrollCohort}). Redirecting to GitHub single sign-on...
            </p>
          </div>
        )}
        <LandingPage
          onLoginGitHub={handleLoginGitHub}
          onLoginWallet={handleLoginWallet}
          onOpenFastTrack={() => setShowFastTrackModal(true)}
          loading={loading}
          error={loginError}
        />
        <FastTrackEnrollmentModal
          isOpen={showFastTrackModal}
          onClose={() => setShowFastTrackModal(false)}
          university={enrollUniversity}
          cohortId={enrollCohort}
          onSuccess={(user) => {
            const uid = user.user_id || user._id;
            setUserId(uid);
            setAuthType('github');
            setProgress(user);
            navigate('/sandbox');
          }}
        />
      </>
    );
  }

  if (isLoggedIn && location.pathname === '/login') {
    return <Navigate to="/academy" replace />;
  }

  return (
    <div className="app-layout">
      <HeadLayoutMeta isLoggedIn={isLoggedIn} activePage={activePage} />
      <Sidebar
        activePage={activePage}
        onNavigate={handleNavigate}
        userId={userId}
        authType={authType}
        onLogout={handleLogout}
        isOpen={mobileNavOpen}
        onClose={() => setMobileNavOpen(false)}
        isLoggedIn={isLoggedIn}
      />
      <Header
        activePage={activePage}
        xp={progress?.xp ?? 0}
        streak={progress?.streak_days ?? 0}
        userId={userId}
        authType={authType}
        progress={progress}
        onLoginGitHub={handleLoginGitHub}
        onLoginWallet={handleLoginWallet}
        onLogout={handleLogout}
        onLinkGitHub={handleLinkGitHub}
        onLinkWallet={handleLinkWallet}
        onOpenFastTrack={() => setShowFastTrackModal(true)}
        isMobileNavOpen={mobileNavOpen}
        onToggleMobileNav={() => setMobileNavOpen((prev) => !prev)}
        isLoggedIn={isLoggedIn}
      />
      <FastTrackEnrollmentModal
        isOpen={showFastTrackModal}
        onClose={() => setShowFastTrackModal(false)}
        university={enrollUniversity}
        cohortId={enrollCohort}
        onSuccess={(user) => {
          const uid = user.user_id || user._id;
          setUserId(uid);
          setAuthType('github');
          setProgress(user);
          navigate('/sandbox');
        }}
      />
      <main className="app-main" id="main-content">
        <Routes>
          <Route path="/" element={<Navigate to={isLoggedIn ? "/academy" : "/"} replace />} />
          <Route path="/login" element={<Navigate to={isLoggedIn ? "/academy" : "/"} replace />} />
          <Route path="/roadmap" element={<Navigate to="/academy" replace />} />
          <Route path="/enroll" element={<Navigate to="/academy" replace />} />
          <Route path="/academy" element={
            selectedLessonId ? (
              <LessonView
                lessonId={selectedLessonId}
                userId={userId}
                onBack={() => setSelectedLessonId(null)}
                onProgressUpdate={handleProgressUpdate}
                token={jwtToken || ''}
                activeTrack={progress?.active_track || 'ethereum'}
              />
            ) : selectedLevel != null ? (
               <LessonsList
                 levelId={selectedLevel}
                 courses={courses}
                 progress={progress}
                 onBack={() => setSelectedLevel(null)}
                 onSelectLesson={setSelectedLessonId}
               />
            ) : (
              <RoadmapPage
                progress={progress}
                loading={loading}
                onSelectLevel={setSelectedLevel}
                userId={userId}
                token={jwtToken || ''}
                onProgressUpdate={handleProgressUpdate}
                isLoggedIn={isLoggedIn}
              />
            )
          } />
          <Route path="/dashboard" element={
            isLoggedIn ? (
              <DashboardPage
                progress={progress}
                loading={loading}
                userId={userId}
                onProgressUpdate={handleProgressUpdate}
                token={jwtToken || ''}
                onNavigate={(page) => navigate(`/${page}`)}
              />
            ) : (
              <Navigate to="/" replace />
            )
          } />
          <Route path="/analytics" element={<Navigate to="/academy" replace />} />
          <Route path="/sandbox" element={<PlaygroundView isLoggedIn={isLoggedIn} />} />
          <Route path="/playground" element={<PlaygroundView isLoggedIn={isLoggedIn} />} />
          <Route path="/forum" element={
            isLoggedIn ? (
              <ForumView userId={userId} token={jwtToken || ''} />
            ) : (
              <Navigate to="/" replace />
            )
          } />
          <Route path="/hackathons" element={
            <HackathonsView
              userId={userId || ''}
              onProgressUpdate={handleProgressUpdate}
              token={jwtToken || ''}
              isLoggedIn={isLoggedIn}
            />
          } />
          <Route path="/careers" element={<CareerDashboard isLoggedIn={isLoggedIn} />} />
          <Route path="/career" element={<CareerDashboard isLoggedIn={isLoggedIn} />} />
          <Route path="/leaderboard" element={<LeaderboardPage />} />
          <Route path="/mentor" element={
            isLoggedIn ? (
              <MentorPage currentLevel={progress?.current_level ?? 1} userId={userId} />
            ) : (
              <Navigate to="/" replace />
            )
          } />
          <Route path="/certificates" element={<CertificatesView userId={userId} isLoggedIn={isLoggedIn} />} />
          <Route path="/subscriptions" element={<SubscriptionPlans isLoggedIn={isLoggedIn} />} />
          <Route path="/subscribe" element={<SubscriptionPlans isLoggedIn={isLoggedIn} />} />
          <Route path="/about" element={<AboutPage isLoggedIn={isLoggedIn} />} />
          <Route path="*" element={<Navigate to={isLoggedIn ? "/academy" : "/"} replace />} />
        </Routes>
        
        <footer className="app-global-footer" style={{ textAlign: 'center', padding: '32px 16px 16px 16px', borderTop: '1px solid rgba(255, 255, 255, 0.06)', fontSize: '0.75rem', color: 'var(--clr-text-muted)', marginTop: '40px' }}>
          © 2026 Morfinance AI. 66 Paul Street, London, EC2A 4NA. All rights reserved. | Enterprise EdTech & Software Architecture Academy
        </footer>
      </main>
    </div>
  );
}
