# 📚 Gaurav's Daily Learning Notes

A fully automated daily learning system — one rich, 500-word note every morning on rotating topics.

| Day | Topic |
|-----|-------|
| Monday | Productivity Book Summary |
| Tuesday | Sales Framework |
| Wednesday | Customer Success |
| Thursday | B2B Tech Update |
| Friday | AI Learnings |
| Saturday | Philosophy |
| Sunday | Science / Physics / Astrophysics / Nature |

---

## ⚙️ Setup (One-Time, ~10 minutes)

### Step 1: Create a GitHub account & new repo
- Go to [github.com](https://github.com) → Sign up or log in
- Click **"New repository"** → name it `daily-learning-notes`
- Set it to **Public** (required for free GitHub Pages)
- Click **Create repository**

### Step 2: Upload these files
Upload all files from this folder into your repo:
- `generate_note.py`
- `.github/workflows/daily-note.yml`
- `README.md`

You can drag-and-drop them directly on GitHub's web UI.

### Step 3: Add your Anthropic API key
- Go to [console.anthropic.com](https://console.anthropic.com) → API Keys → Create key
- In your GitHub repo → **Settings → Secrets and variables → Actions**
- Click **New repository secret**
- Name: `ANTHROPIC_API_KEY`
- Value: paste your key
- Click **Add secret**

### Step 4: Enable GitHub Pages
- In your repo → **Settings → Pages**
- Source: **Deploy from a branch**
- Branch: `main` / folder: `/notes`
- Click **Save**

Your public URL will be:
`https://YOUR-GITHUB-USERNAME.github.io/daily-learning-notes/`

### Step 5: Test it manually
- Go to your repo → **Actions** tab
- Click **Daily Learning Note** → **Run workflow**
- Watch it run — your first note will appear in `/notes/` within ~30 seconds

---

## 💰 Cost

- GitHub: **Free**
- GitHub Pages: **Free**
- Claude API (Haiku model): **~₹5–10/month**

---

## 🔧 Customisation

**Change the time:** Edit the `cron` line in `.github/workflows/daily-note.yml`
- `'30 1 * * *'` = 7:00 AM IST
- Use [crontab.guru](https://crontab.guru) to calculate UTC times

**Upgrade model:** In `generate_note.py`, change `claude-haiku-4-5-20251001` to `claude-sonnet-4-20250514` for richer writing (~10x cost)

**Add topics:** Edit the `TOPICS` dict in `generate_note.py`
