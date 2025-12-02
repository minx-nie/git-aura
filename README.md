# 🌌 Git-Aura

<div align="center">

![Git-Aura Banner](https://img.shields.io/badge/Git--Aura-Generative%20Art-blueviolet?style=for-the-badge&logo=github)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)](https://python.org)
[![GitHub Actions](https://img.shields.io/github/actions/workflow/status/ThanhNguyxn/git-aura/aura.yml?style=flat-square&label=Aura%20Generation)](https://github.com/ThanhNguyxn/git-aura/actions)

**Transform your GitHub activity into a unique, mathematically-derived piece of generative art.**

<img src="aura.svg" alt="Git Aura Example" width="450" />

*Your code has a soul. This is its aura.* ✨

</div>

---

## 🎯 What is Git-Aura?

Git-Aura analyzes your GitHub statistics and creates a **beautiful, animated SVG visualization** — your coding "aura". No more boring bar charts. This is **art derived from math**.

### ✨ Features

| Feature | Description |
|---------|-------------|
| 🎨 **Unique Identity** | Each aura is deterministically generated from your GitHub user ID |
| 🌈 **Language Colors** | Color palette derived from your top programming languages |
| 🌀 **Particle Flow** | Organic curves using Simplex noise algorithms |
| 💫 **Activity Glow** | Commit streaks influence the glow intensity |
| 🌙 **Dark Mode** | Designed for GitHub's dark theme |
| 🔄 **Auto Updates** | GitHub Action keeps your aura fresh daily |

---

## 🚀 Quick Start

### ⚠️ Prerequisites (IMPORTANT!)

> **You MUST complete this step first, or the workflow will fail!**

<details open>
<summary>🔑 <strong>Step 1: Create Personal Access Token (PAT)</strong></summary>

The default `GITHUB_TOKEN` cannot read user contribution data. Create a PAT:

1. 🔗 Go to **[github.com/settings/tokens/new](https://github.com/settings/tokens/new?description=git-aura&scopes=read:user)**
2. ✏️ **Note:** `git-aura`
3. ⏰ **Expiration:** 90 days (or custom)
4. ☑️ **Select scope:** `read:user`
5. 🟢 Click **"Generate token"**
6. 📋 **Copy the token** (starts with `ghp_...`)

</details>

<details open>
<summary>🔐 <strong>Step 2: Add Token to Your Repository</strong></summary>

1. Go to your **forked repository**
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"**
4. Fill in:
   | Field | Value |
   |-------|-------|
   | **Name** | `GH_PAT` |
   | **Secret** | *paste your token* |
5. Click **"Add secret"** ✅

</details>

---

### 🍴 Option 1: Fork & Use (Recommended)

```
┌─────────────────────────────────────────────────────────────┐
│  1️⃣  Fork this repository                                   │
│       └──▶ Click "Fork" button above                        │
│                                                             │
│  2️⃣  Add GH_PAT secret (see Prerequisites ☝️)               │
│       └──▶ Settings → Secrets → Actions → New secret        │
│                                                             │
│  3️⃣  Run the workflow                                       │
│       └──▶ Actions → "Generate Git Aura" → "Run workflow"   │
│                                                             │
│  4️⃣  Done! Your aura.svg is generated 🎉                    │
└─────────────────────────────────────────────────────────────┘
```

#### 📝 Add to Your Profile README:

```markdown
![My Git Aura](https://raw.githubusercontent.com/YOUR_USERNAME/git-aura/main/aura.svg)
```

---

### 💻 Option 2: Run Locally

```bash
# 1. Clone the repository
git clone https://github.com/ThanhNguyxn/git-aura.git
cd git-aura

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your GitHub token (with read:user scope)
export GITHUB_TOKEN="ghp_your_token_here"

# 4. Generate your aura! 🎨
python main.py YOUR_USERNAME -o my-aura.svg
```

---

## 📖 How It Works

### 🧮 The Math Behind Your Aura

Your GitHub activity is treated as a **feature vector** and transformed through mathematical functions:

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  📊 GitHub Data │ ──▶ │  🔢 Normalize    │ ──▶ │  🎨 Visual      │
│                 │     │                  │     │                 │
│ • Commits       │     │ • Log scaling    │     │ • Particle      │
│ • Streak        │     │ • Sigmoid        │     │   density       │
│ • Languages     │     │ • Entropy        │     │ • Glow effect   │
│ • Commit times  │     │ • Color blend    │     │ • Flow chaos    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

| Metric | Formula | Visual Effect |
|--------|---------|---------------|
| Total Commits | $\rho = \log(commits)$ | Particle density |
| Max Streak | $I = \sigma(streak/365)$ | Glow intensity |
| Commit Times | $\chi = H(distribution)$ | Flow turbulence |
| Languages | Weighted RGB average | Color palette |

> **Legend:**
> - $\sigma$ = Sigmoid function for smooth normalization
> - $H$ = Shannon entropy for chaos measurement

### 🌀 The Generative Engine

```
     🌱 Initialize                    🌊 Flow Field
    ┌───────────┐                  ┌───────────────┐
    │ Fibonacci │                  │ Simplex Noise │
    │  Spiral   │ ──── drives ───▶│   Vectors     │
    └───────────┘                  └───────────────┘
          │                               │
          ▼                               ▼
    ┌───────────┐                  ┌───────────────┐
    │ Particles │ ◀── guided by ──│ Force Field   │
    └───────────┘                  └───────────────┘
          │
          ▼
    ┌───────────────┐
    │   SVG Paths   │ ──▶ 🎨 Final Aura
    └───────────────┘
```

---

## ⚙️ Configuration

### 🖥️ CLI Options

```bash
python main.py [USERNAME] [OPTIONS]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `USERNAME` | `$GITHUB_ACTOR` | GitHub username |
| `-o, --output` | `aura.svg` | Output file path |
| `-w, --width` | `800` | SVG width (px) |
| `-H, --height` | `800` | SVG height (px) |
| `--no-animation` | `false` | Disable CSS animation |
| `--check-changes` | `false` | Only save if changed |
| `-v, --verbose` | `false` | Debug logging |

### 🔐 Environment Variables

| Variable | Required | Description |
|:--------:|:--------:|-------------|
| `GITHUB_TOKEN` | ✅ | PAT with `read:user` scope |
| `GITHUB_ACTOR` | ❌ | Default username (auto-set in Actions) |

---

## 🔧 GitHub Action

### ⏰ Schedule

The workflow runs **daily at midnight UTC**. Customize in `.github/workflows/aura.yml`:

```yaml
on:
  schedule:
    - cron: '0 0 * * *'  # ← Modify schedule here
```

### 🔒 Required Secrets

| Secret Name | Required | How to Get |
|-------------|:--------:|------------|
| `GH_PAT` | ✅ | [Create token](https://github.com/settings/tokens/new?scopes=read:user) with `read:user` |

### 🚫 Preventing History Bloat

The workflow compares file hashes before committing:
- ✅ **Changed** → Commit & push
- ⏭️ **Same** → Skip commit

---

## 🎨 Customization

### 📐 Canvas Sizes

```bash
# Square (default)
python main.py username -w 800 -H 800

# Wide banner
python main.py username -w 1200 -H 400

# Vertical
python main.py username -w 400 -H 800
```

### 🖼️ Profile README Example

```markdown
<div align="center">
  <img src="https://raw.githubusercontent.com/YOUR_USERNAME/git-aura/main/aura.svg" width="400" />
  <br/>
  <i>My coding aura ✨</i>
</div>
```

---

## 📁 Project Structure

```
git-aura/
├── 📂 .github/
│   └── 📂 workflows/
│       └── 📄 aura.yml          # 🔄 Daily generation workflow
├── 📂 src/
│   ├── 📄 __init__.py           # 📦 Package init
│   ├── 📄 data_loader.py        # 🔌 GitHub GraphQL API
│   ├── 📄 generative_engine.py  # 🌀 Particle system & noise
│   └── 📄 renderer.py           # 🎨 SVG generation
├── 📄 main.py                   # 🚀 Entry point
├── 📄 requirements.txt          # 📋 Dependencies
├── 📄 README.md                 # 📖 You are here!
└── 🖼️ aura.svg                  # ✨ Generated output
```

---

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| ![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white) | Core language |
| ![NumPy](https://img.shields.io/badge/NumPy-013243?style=flat-square&logo=numpy&logoColor=white) | Vector mathematics |
| **svgwrite** | SVG generation |
| **OpenSimplex** | Noise functions |
| **requests** | GitHub API calls |

---

## ❓ Troubleshooting

<details>
<summary>🔴 <strong>Workflow fails with "GraphQL errors" or exit code 1</strong></summary>

**Cause:** Missing or invalid `GH_PAT` secret.

**Solution:**
1. ✅ Check if `GH_PAT` secret exists: Settings → Secrets → Actions
2. ✅ Ensure your token has `read:user` scope
3. ✅ Token might be expired — regenerate if needed
4. ✅ Re-run the workflow after adding the secret

</details>

<details>
<summary>🔴 <strong>No aura.svg generated</strong></summary>

**Cause:** Workflow completed but file not committed.

**Solution:**
1. Check Actions log for errors
2. Verify `contents: write` permission in workflow
3. Try running workflow manually

</details>

<details>
<summary>🔴 <strong>Aura looks empty or minimal</strong></summary>

**Cause:** Low GitHub activity or new account.

**Solution:** This is expected! Your aura grows with your contributions. Keep coding! 💪

</details>

---

## 📄 License

```
MIT License - feel free to fork, modify, and share!
```

---

## 🙏 Credits

<div align="center">

Created with 💜 by [@ThanhNguyxn](https://github.com/ThanhNguyxn)

Inspired by the beauty of mathematical visualization and the art of code.

---

⭐ **Star this repo if you like it!** ⭐

[Report Bug](https://github.com/ThanhNguyxn/git-aura/issues) · [Request Feature](https://github.com/ThanhNguyxn/git-aura/issues)

</div>
