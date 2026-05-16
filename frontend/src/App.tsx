
import ResumeScanner from './components/ResumeScanner.tsx'
import './App.css'
import { useState } from 'react';
import { VideoUploadPage } from './components/VideoUploadPage';
//import { getTier } from './utils/auth';

function App() {
  const [activeTab, setActiveTab] = useState<'resume' | 'video'>('resume');
  //const tier = getTier();

  return (
    <>
      {/* Tab navigation */}
      <div style={{ display: "flex", gap: "8px", padding: "4px", background: "var(--surface)", borderRadius: "12px", border: "1px solid var(--border)", marginBottom: "24px", width: "fit-content", margin: "40px auto 0 auto" }}>
        <button
          onClick={() => setActiveTab('resume')}
          style={{
            padding: "10px 20px",
            borderRadius: "8px",
            fontSize: "13px",
            fontFamily: "var(--font-mono)",
            fontWeight: activeTab === 'resume' ? 600 : 400,
            background: activeTab === 'resume' ? "var(--border-hi)" : "transparent",
            color: activeTab === 'resume' ? "var(--text)" : "var(--muted)",
            border: "none",
            cursor: "pointer",
            transition: "all 0.2s"
          }}
        >
          {/* Show only when NOT active */}
          {activeTab !== "resume" && (
            <span
              style={{
                color: "var(--accent)",
                fontSize: "10px",
                marginRight: "6px"
              }}
            >
              ✦
            </span>
          )}
          Resume Scanner

        </button>
        <button
          onClick={() => setActiveTab('video')}
          style={{
            padding: "10px 20px",
            borderRadius: "8px",
            fontSize: "13px",
            fontFamily: "var(--font-mono)",
            fontWeight: activeTab === 'video' ? 600 : 400,
            background: activeTab === 'video' ? "var(--border-hi)" : "transparent",
            color: activeTab === 'video' ? "var(--text)" : "var(--muted)",
            border: "none",
            cursor: "pointer",
            transition: "all 0.2s"
          }}
        >
          Interview Coach
          {/* Show only when NOT active */}
          {activeTab !== "video" && (
            <span
              style={{
                color: "var(--accent2)",
                fontSize: "10px",
                marginLeft: "6px"
              }}
            >
              ✦
            </span>
          )}
        </button>
      </div>

      {/* Tab panels */}
      {activeTab === 'resume' && (
        // your existing ResumeScanner JSX here
        <ResumeScanner />
      )}
      {activeTab === 'video' && (
        <VideoUploadPage />
      )}






    </>
  )
}

export default App