// ─── HeadLayoutMeta component — manages document head title and meta tags based on layout state ───
import React, { useEffect } from 'react';
import type { NavPage } from '../../types';

export interface HeadLayoutMetaProps {
  isLoggedIn: boolean;
  activePage?: NavPage;
}

const PAGE_TITLES: Record<NavPage, string> = {
  academy: 'Curriculum & Roadmap',
  roadmap: 'Curriculum & Roadmap',
  dashboard: 'Engineering Dashboard',
  analytics: 'Cohort Analytics',
  sandbox: 'Multi-Runtime Sandbox IDE',
  forum: 'Developer Forum',
  hackathons: 'Technical Sprints & Grants',
  careers: 'Career Opportunities',
  leaderboard: 'Developer Leaderboard',
  mentor: 'AI Mentor Workspace',
  certificates: 'System Credentials',
  subscriptions: 'Subscription Plans',
  about: 'About Mor Academy',
};

export const HeadLayoutMeta: React.FC<HeadLayoutMetaProps> = ({ isLoggedIn, activePage }) => {
  useEffect(() => {
    // 1. Update document title
    const baseTitle = 'Developer Academy';
    if (isLoggedIn && activePage && PAGE_TITLES[activePage]) {
      document.title = `${PAGE_TITLES[activePage]} — ${baseTitle}`;
    } else if (isLoggedIn) {
      document.title = `${baseTitle} — Advanced Software Architecture & Systems`;
    } else {
      document.title = `${baseTitle} — Enterprise EdTech & Advanced Software Architectures`;
    }

    // Helper to safely set or create meta tags
    const setMetaTag = (attrName: string, attrVal: string, content: string) => {
      let meta = document.querySelector(`meta[${attrName}="${attrVal}"]`);
      if (!meta) {
        meta = document.createElement('meta');
        meta.setAttribute(attrName, attrVal);
        document.head.appendChild(meta);
      }
      meta.setAttribute('content', content);
    };

    // 2. Update meta description
    const descContent = isLoggedIn
      ? 'Developer Academy — Universal curriculum and interactive sandbox for high-performance software logic and distributed enterprise applications.'
      : 'Master advanced object-oriented logic and enterprise software design with MOR Developer Academy. The primary portal for systems infrastructure developers, cloud layout engineering, and distributed architecture frameworks.';
    setMetaTag('name', 'description', descContent);

    // 3. Update meta keywords
    const keywordsContent = isLoggedIn
      ? 'Enterprise EdTech, Distributed Systems, Software Engineering, Architecture, Compilers, Developer Education'
      : 'Enterprise EdTech, Distributed Systems Programming, Advanced Data Architectures, Open-Source Software, FinTech Tooling, SaaS Sandbox, Developer Education';
    setMetaTag('name', 'keywords', keywordsContent);

    // 4. Update OpenGraph tags
    const ogTitleContent = isLoggedIn
      ? (activePage && PAGE_TITLES[activePage] ? `${PAGE_TITLES[activePage]} — ${baseTitle}` : `${baseTitle} — Advanced Software Architecture & Systems`)
      : 'Developer Academy — Distributed Systems Programming & Advanced Data Architectures';
    setMetaTag('property', 'og:title', ogTitleContent);

    const ogDescContent = isLoggedIn
      ? 'Developer Academy — Universal curriculum and interactive sandbox for high-performance software logic and distributed enterprise applications.'
      : 'Master advanced object-oriented logic and enterprise software design with MOR Developer Academy. The primary portal for systems infrastructure developers, cloud layout engineering, and distributed architecture frameworks.';
    setMetaTag('property', 'og:description', ogDescContent);

  }, [isLoggedIn, activePage]);

  return null;
};

export default HeadLayoutMeta;
