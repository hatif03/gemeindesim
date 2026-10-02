# GemeindeSim — repo setup

## What was done

1. Cloned [HackApertus/project-template](https://github.com/HackApertus/project-template) to  
   **`C:\Users\mdhat\Desktop\gemeindesim`**
2. Removed tracks **1A, 1B, 2A**; kept **`track_2b/`** for **Track 2B — Own Project**
3. Renamed the project **GemeindeSim** (multilingual Swiss civic simulation)
4. Added hackathon context, probe report, Docker stub, and Python package skeleton

Template remote is **`template-upstream`** (not `origin`). Add your own GitHub repo as `origin` when you fork.

## Fork on GitHub (recommended)

1. Open https://github.com/HackApertus/project-template and click **Use this template** → create **`gemeindesim`** (or fork this local tree after first push).
2. In PowerShell:

```powershell
cd C:\Users\mdhat\Desktop\gemeindesim
git add -A
git commit -m "Initialize GemeindeSim from Hack Apertus template (Track 2B)"
git remote add origin https://github.com/YOUR_USER/gemeindesim.git
git push -u origin main
```

3. Set the repository **public** (Settings → Visibility) before submission.

## Local config

```powershell
cd C:\Users\mdhat\Desktop\gemeindesim\track_2b
copy .env.example .env
# Edit .env — set LLM_API_KEY (never commit)
```

## Run (once Docker is available)

```powershell
cd C:\Users\mdhat\Desktop\gemeindesim
make run
```

Current container runs a **stub** that checks env vars; simulation code goes in `track_2b/src/gemeindesim/`.

## Key docs

| File | Purpose |
| --- | --- |
| `track_2b/docs/HACKATHON.md` | Deadlines, links, submission checklist |
| `track_2b/docs/PROBE-AND-PLAN.md` | Apertus probe + engineering plan |
| `track_2b/docs/ARCHITECTURE.md` | Module sketch |
| `track_2b/technical_report.md` | Submission report (export to PDF) |

Study repo (separate): `C:\Users\mdhat\Desktop\apertus\`
