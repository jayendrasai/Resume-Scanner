
// import ResumeScanner from './components/ResumeScanner.tsx'
// import './App.css'
// import { useState } from 'react';
// import { VideoUploadPage } from './components/VideoUploadPage';
// //import { getTier } from './utils/auth';

// function App() {
//   const [activeTab, setActiveTab] = useState<'resume' | 'video'>('resume');
//   //const tier = getTier();

//   return (
//     <>
//       {/* Tab navigation */}
//       <div style={{ display: "flex", gap: "8px", padding: "4px", background: "var(--surface)", borderRadius: "12px", border: "1px solid var(--border)", marginBottom: "24px", width: "fit-content", margin: "40px auto 0 auto" }}>
//         <button
//           onClick={() => setActiveTab('resume')}
//           style={{
//             padding: "10px 20px",
//             borderRadius: "8px",
//             fontSize: "13px",
//             fontFamily: "var(--font-mono)",
//             fontWeight: activeTab === 'resume' ? 600 : 400,
//             background: activeTab === 'resume' ? "var(--border-hi)" : "transparent",
//             color: activeTab === 'resume' ? "var(--text)" : "var(--muted)",
//             border: "none",
//             cursor: "pointer",
//             transition: "all 0.2s"
//           }}
//         >
//           {/* Show only when NOT active */}
//           {activeTab !== "resume" && (
//             <span
//               style={{
//                 color: "var(--accent)",
//                 fontSize: "10px",
//                 marginRight: "6px"
//               }}
//             >
//               ✦
//             </span>
//           )}
//           Resume Scanner

//         </button>
//         <button
//           onClick={() => setActiveTab('video')}
//           style={{
//             padding: "10px 20px",
//             borderRadius: "8px",
//             fontSize: "13px",
//             fontFamily: "var(--font-mono)",
//             fontWeight: activeTab === 'video' ? 600 : 400,
//             background: activeTab === 'video' ? "var(--border-hi)" : "transparent",
//             color: activeTab === 'video' ? "var(--text)" : "var(--muted)",
//             border: "none",
//             cursor: "pointer",
//             transition: "all 0.2s"
//           }}
//         >
//           Interview Coach
//           {/* Show only when NOT active */}
//           {activeTab !== "video" && (
//             <span
//               style={{
//                 color: "var(--accent2)",
//                 fontSize: "10px",
//                 marginLeft: "6px"
//               }}
//             >
//               ✦
//             </span>
//           )}
//         </button>
//       </div>

//       {/* Tab panels */}
//       {activeTab === 'resume' && (
//         // your existing ResumeScanner JSX here
//         <ResumeScanner />
//       )}
//       {activeTab === 'video' && (
//         <VideoUploadPage />
//       )}






//     </>
//   )
// }

// export default App


import { useState } from 'react';
import ResumeScanner from './components/ResumeScanner.tsx';
import { VideoUploadPage } from './components/VideoUploadPage';
import { AuthPage } from './components/AuthPage';
import { AccountPage } from './components/AccountPage';
import { GlobalStyle } from './styles/GlobalStyles';
import { isAuthenticated, getTier } from './utils/auth';
import './App.css';

type AppTab = 'resume' | 'video' | 'account';

function App() {
  const [authed, setAuthed] = useState(isAuthenticated());
  const [activeTab, setActiveTab] = useState<AppTab>('resume');
  const [, forceUpdate] = useState(0);

  const tier = getTier();

  const handleAuth = () => {
    setAuthed(true);
    forceUpdate(n => n + 1);
  };

  const handleSignOut = () => {
    setAuthed(false);
    setActiveTab('resume');
  };

  // Tab button factory — avoids repetition
  const TabBtn = ({
    id, label, badge
  }: { id: AppTab; label: string; badge?: string }) => (
    <button
      onClick={() => setActiveTab(id)}
      style={{
        padding: '10px 20px',
        borderRadius: '8px',
        fontSize: '13px',
        fontFamily: 'var(--font-mono)',
        fontWeight: activeTab === id ? 600 : 400,
        background: activeTab === id ? 'var(--border-hi)' : 'transparent',
        color: activeTab === id ? 'var(--text)' : 'var(--muted)',
        border: 'none',
        cursor: 'pointer',
        transition: 'all 0.2s',
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
      }}
    >
      {activeTab !== id && id === 'resume' && (
        <span style={{ color: 'var(--accent)', fontSize: '10px' }}>✦</span>
      )}
      {label}
      {activeTab !== id && id === 'video' && (
        <span style={{ color: 'var(--accent2)', fontSize: '10px' }}>✦</span>
      )}
      {badge && (
        <span style={{
          fontSize: '10px',
          background: 'rgba(200,240,74,0.12)',
          color: 'var(--accent)',
          border: '1px solid rgba(200,240,74,0.2)',
          borderRadius: '20px',
          padding: '1px 6px',
          fontFamily: 'var(--font-mono)',
        }}>
          {badge}
        </span>
      )}
    </button>
  );

  // Not authenticated — show auth page, no tabs
  if (!authed) {
    return (
      <>
        <GlobalStyle />
        <AuthPage onAuth={handleAuth} />
      </>
    );
  }

  return (
    <>
      <GlobalStyle />

      {/* Tab navigation */}
      <div style={{
        display: 'flex',
        gap: '8px',
        padding: '4px',
        background: 'var(--surface)',
        borderRadius: '12px',
        border: '1px solid var(--border)',
        width: 'fit-content',
        margin: '40px auto 32px auto',
        position: 'relative',
        zIndex: 1,
      }}>
        <TabBtn id="resume" label="Resume Scanner" />
        <TabBtn
          id="video"
          label="Interview Coach"
          badge={tier !== 'premium' ? 'PRO' : undefined}
        />
        <TabBtn id="account" label="Account" />
      </div>

      {/* Tab panels */}
      <div style={{ position: 'relative', zIndex: 1 }}>
        {activeTab === 'resume' && <ResumeScanner />}
        {activeTab === 'video' && <VideoUploadPage />}
        {activeTab === 'account' && (
          <AccountPage onSignOut={handleSignOut} />
        )}
      </div>
    </>
  );
}

export default App;