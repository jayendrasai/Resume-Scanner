// const GlobalStyle = () => (
<style>{`
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300&display=swap');

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg:        #0b0c0f;
      --surface:   #111318;
      --border:    #1f2229;
      --border-hi: #2e3340;
      --accent:    #c8f04a;
      --accent2:   #4af0c8;
      --text:      #e8eaf0;
      --muted:     #5a5f72;
      --danger:    #f04a6a;
      --warn:      #f0a84a;
      --font-head: 'Syne', sans-serif;
      --font-mono: 'DM Mono', monospace;
    }

    body {
      background: var(--bg);
      color: var(--text);
      font-family: var(--font-mono);
      min-height: 100vh;
    }

    /* Noise overlay */
    body::before {
      content: '';
      position: fixed; inset: 0; z-index: 0;
      background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E");
      pointer-events: none;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: var(--bg); }
    ::-webkit-scrollbar-thumb { background: var(--border-hi); border-radius: 2px; }

    @keyframes fadeUp {
      from { opacity: 0; transform: translateY(18px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes pulse-ring {
      0%   { transform: scale(1);   opacity: .6; }
      70%  { transform: scale(1.3); opacity: 0; }
      100% { transform: scale(1);   opacity: 0; }
    }
    @keyframes scan-line {
      from { transform: translateY(-100%); }
      to   { transform: translateY(400%); }
    }
    @keyframes score-fill {
      from { stroke-dashoffset: 289; }
    }
    @keyframes blink { 50% { opacity: 0; } }

    .fade-up { animation: fadeUp .45s ease both; }
    .fade-up-2 { animation: fadeUp .45s .1s ease both; }
    .fade-up-3 { animation: fadeUp .45s .2s ease both; }
  `}</style>
// );

// export default GlobalStyle;

import React from 'react';

export const GlobalStyle: React.FC = () => (
  // <style>{`
  //   @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300&display=swap');
  //   /* ... rest of your CSS ... */
  // `}</style>
  <style>{`
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300&display=swap');

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg:        #0b0c0f;
      --surface:   #111318;
      --border:    #1f2229;
      --border-hi: #2e3340;
      --accent:    #c8f04a;
      --accent2:   #4af0c8;
      --text:      #e8eaf0;
      --muted:     #5a5f72;
      --danger:    #f04a6a;
      --warn:      #f0a84a;
      --font-head: 'Syne', sans-serif;
      --font-mono: 'DM Mono', monospace;
    }

    body {
      background: var(--bg);
      color: var(--text);
      font-family: var(--font-mono);
      min-height: 100vh;
    }

    /* Noise overlay */
    body::before {
      content: '';
      position: fixed; inset: 0; z-index: 0;
      background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E");
      pointer-events: none;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: var(--bg); }
    ::-webkit-scrollbar-thumb { background: var(--border-hi); border-radius: 2px; }

    @keyframes fadeUp {
      from { opacity: 0; transform: translateY(18px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes pulse-ring {
      0%   { transform: scale(1);   opacity: .6; }
      70%  { transform: scale(1.3); opacity: 0; }
      100% { transform: scale(1);   opacity: 0; }
    }
    @keyframes scan-line {
      from { transform: translateY(-100%); }
      to   { transform: translateY(400%); }
    }
    @keyframes score-fill {
      from { stroke-dashoffset: 289; }
    }
    @keyframes blink { 50% { opacity: 0; } }

    .fade-up { animation: fadeUp .45s ease both; }
    .fade-up-2 { animation: fadeUp .45s .1s ease both; }
    .fade-up-3 { animation: fadeUp .45s .2s ease both; }
  `}</style>
);