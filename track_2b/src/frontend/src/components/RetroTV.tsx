"use client";

export default function RetroTV() {
  return (
    <>
      <style>{`
        @keyframes rgb-drift {
          0%   { transform: translateX(0px); }
          20%  { transform: translateX(1.2px); }
          40%  { transform: translateX(-1.0px); }
          60%  { transform: translateX(0.8px); }
          80%  { transform: translateX(-1.2px); }
          100% { transform: translateX(0px); }
        }

        @keyframes global-flicker {
          0% { opacity: 0.98; }
          5% { opacity: 0.95; }
          10% { opacity: 0.99; }
          15% { opacity: 0.93; }
          20% { opacity: 0.98; }
          25% { opacity: 0.94; }
          30% { opacity: 0.99; }
          35% { opacity: 0.92; }
          40% { opacity: 0.97; }
          45% { opacity: 0.95; }
          50% { opacity: 0.98; }
          55% { opacity: 0.94; }
          60% { opacity: 0.99; }
          65% { opacity: 0.93; }
          70% { opacity: 0.98; }
          75% { opacity: 0.94; }
          80% { opacity: 0.99; }
          85% { opacity: 0.92; }
          90% { opacity: 0.97; }
          95% { opacity: 0.95; }
          100% { opacity: 0.98; }
        }

        @keyframes v-sync-glitch {
          0% { transform: translateY(-100%); opacity: 0; }
          10% { transform: translateY(-100%); opacity: 0; }
          11% { transform: translateY(-100%); opacity: 0.3; }
          25% { transform: translateY(100vh); opacity: 0.3; }
          26% { transform: translateY(100vh); opacity: 0; }
          100% { transform: translateY(100vh); opacity: 0; }
        }

        /* A — medium, moderate brightness */
        @keyframes strobe-a {
          0%   { opacity: 0.00; }
          12%  { opacity: 0.25; }
          13%  { opacity: 0.00; }
          45%  { opacity: 0.30; }
          46%  { opacity: 0.03; }
          72%  { opacity: 0.00; }
          90%  { opacity: 0.20; }
          100% { opacity: 0.00; }
        }
        /* B — very large, near invisible */
        @keyframes strobe-b {
          0%   { opacity: 0.00; }
          20%  { opacity: 0.08; }
          50%  { opacity: 0.00; }
          80%  { opacity: 0.10; }
          100% { opacity: 0.02; }
        }
        /* C — tall narrow strip, slightly brighter */
        @keyframes strobe-c {
          0%   { opacity: 0.00; }
          15%  { opacity: 0.28; }
          16%  { opacity: 0.00; }
          45%  { opacity: 0.18; }
          46%  { opacity: 0.00; }
          75%  { opacity: 0.22; }
          76%  { opacity: 0.05; }
          100% { opacity: 0.00; }
        }
        /* D — enormous, barely visible */
        @keyframes strobe-d {
          0%   { opacity: 0.05; }
          35%  { opacity: 0.00; }
          70%  { opacity: 0.08; }
          100% { opacity: 0.00; }
        }
        /* E — wide short band, moderate */
        @keyframes strobe-e {
          0%   { opacity: 0.12; }
          25%  { opacity: 0.00; }
          55%  { opacity: 0.22; }
          56%  { opacity: 0.05; }
          80%  { opacity: 0.00; }
          100% { opacity: 0.18; }
        }

        .retro-tv-root-bg {
          position: fixed;
          inset: 0;
          z-index: 5;
          pointer-events: none;
          animation: global-flicker 0.15s infinite;
        }

        .retro-tv-root-fg {
          position: fixed;
          inset: 0;
          z-index: 50;
          pointer-events: none;
          animation: global-flicker 0.15s infinite;
        }

        /* Scanlines */
        .retro-tv-scanlines {
          position: absolute;
          inset: 0;
          pointer-events: none;
          background: repeating-linear-gradient(
            to bottom,
            transparent 0px,
            transparent 1px,
            rgba(0, 0, 0, 0.25) 1px,
            rgba(0, 0, 0, 0.25) 2px
          );
        }

        /* Vignette */
        .retro-tv-vignette {
          position: absolute;
          inset: 0;
          pointer-events: none;
          background: radial-gradient(
            ellipse at center,
            transparent 40%,
            rgba(0, 0, 0, 0.65) 80%,
            rgba(0, 0, 0, 0.95) 100%
          );
        }

        /* RGB shift — red channel ghost */
        .retro-tv-rgb-r {
          position: absolute;
          inset: 0;
          pointer-events: none;
          background: repeating-linear-gradient(
            to bottom,
            transparent 0px,
            transparent 2px,
            rgba(255, 0, 0, 0.05) 2px,
            rgba(255, 0, 0, 0.05) 4px
          );
          mix-blend-mode: screen;
          transform: translateX(2.5px);
          animation: rgb-drift 6s ease-in-out infinite;
        }

        /* RGB shift — blue channel ghost */
        .retro-tv-rgb-b {
          position: absolute;
          inset: 0;
          pointer-events: none;
          background: repeating-linear-gradient(
            to bottom,
            transparent 0px,
            transparent 2px,
            rgba(0, 80, 255, 0.05) 2px,
            rgba(0, 80, 255, 0.05) 4px
          );
          mix-blend-mode: screen;
          transform: translateX(-2.5px);
          animation: rgb-drift 6s ease-in-out infinite reverse;
        }

        /* Phosphor noise grain */
        .retro-tv-noise {
          position: absolute;
          inset: 0;
          pointer-events: none;
          opacity: 0.08;
          background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
          background-size: 100px 100px;
        }

        /* V-Sync glitch line */
        .retro-tv-v-sync {
          position: absolute;
          left: 0;
          right: 0;
          height: 15vh;
          background: linear-gradient(to bottom, transparent, rgba(255, 255, 255, 0.05), transparent);
          filter: blur(10px);
          animation: v-sync-glitch 12s linear infinite;
        }

        .retro-tv-strobe {
          position: absolute;
          pointer-events: none;
          mix-blend-mode: screen;
        }

        /* A — irregular oval, upper-left quadrant */
        .retro-tv-strobe-a {
          width: 42vw;
          height: 58vh;
          top: -8%;
          left: 5%;
          border-radius: 38% 62% 55% 45% / 60% 44% 56% 40%;
          background: radial-gradient(ellipse 60% 80% at 40% 50%, rgba(255,255,255,1) 0%, transparent 70%);
          filter: blur(60px);
          animation: strobe-a 4s steps(1) infinite;
        }
        /* B — enormous diffuse cloud, nearly full screen, near invisible */
        .retro-tv-strobe-b {
          width: 140vw;
          height: 130vh;
          top: -15%;
          left: -20%;
          border-radius: 50%;
          background: radial-gradient(ellipse at 55% 45%, rgba(255,255,255,1) 0%, transparent 60%);
          filter: blur(120px);
          animation: strobe-b 11s steps(1) infinite;
        }
        /* C — tall thin vertical smear, right side */
        .retro-tv-strobe-c {
          width: 18vw;
          height: 90vh;
          top: 5%;
          right: 12%;
          border-radius: 50% 50% 40% 60% / 30% 30% 70% 70%;
          background: radial-gradient(ellipse 40% 100% at 50% 40%, rgba(255,255,255,1) 0%, transparent 65%);
          filter: blur(50px);
          animation: strobe-c 3s steps(1) infinite;
        }
        /* D — enormous low-opacity wash, bottom half */
        .retro-tv-strobe-d {
          width: 160vw;
          height: 80vh;
          bottom: -20%;
          left: -30%;
          border-radius: 40% 60% 30% 70% / 50% 50% 50% 50%;
          background: radial-gradient(ellipse 70% 60% at 45% 60%, rgba(255,255,255,1) 0%, transparent 55%);
          filter: blur(140px);
          animation: strobe-d 14s steps(1) infinite;
        }
        /* E — wide flat horizontal band, center */
        .retro-tv-strobe-e {
          width: 80vw;
          height: 28vh;
          top: 38%;
          left: 10%;
          border-radius: 50% 50% 50% 50% / 80% 80% 20% 20%;
          background: radial-gradient(ellipse 100% 50% at 50% 50%, rgba(255,255,255,1) 0%, transparent 70%);
          filter: blur(80px);
          animation: strobe-e 6s steps(1) infinite;
        }
      `}</style>

      <div className="retro-tv-root-bg">
        <div className="retro-tv-v-sync" />
        <div className="retro-tv-strobe retro-tv-strobe-a" />
        <div className="retro-tv-strobe retro-tv-strobe-b" />
        <div className="retro-tv-strobe retro-tv-strobe-c" />
        <div className="retro-tv-strobe retro-tv-strobe-d" />
        <div className="retro-tv-strobe retro-tv-strobe-e" />
      </div>

      <div className="retro-tv-root-fg">
        <div className="retro-tv-scanlines" />
        <div className="retro-tv-vignette" />
        <div className="retro-tv-rgb-r" />
        <div className="retro-tv-rgb-b" />
        <div className="retro-tv-noise" />
      </div>
    </>
  );
}
