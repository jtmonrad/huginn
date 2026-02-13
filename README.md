# Huginn

Automated weekly newsletters powered by Claude, managed from a web UI.

Each newsletter runs on its own schedule via GitHub Actions. You manage everything — prompts, recipients, send times — through a browser-based dashboard hosted on GitHub Pages.

## Setup

### Enable GitHub Pages

1. In this repository, go to **Settings** → **Pages**
2. Under "Source," select **Deploy from a branch**
3. Branch: **main**, folder: **/ (root)**
4. Click **Save**
5. After 1–2 minutes, the app will be live at: `https://jtmonrad.github.io/huginn/`

### Enable GitHub Actions

1. Go to the **Actions** tab
2. If prompted, click **I understand my workflows, go ahead and enable them**

### Open the app

1. Visit `https://jtmonrad.github.io/huginn/`
2. Enter `jtmonrad/huginn` as the repository
3. Enter a **fine-grained Personal Access Token** with Contents + Actions read/write permissions for this repo (the app walks you through creating one)
4. Click **Connect**

The biosecurity newsletter is already configured and will send every Monday at 8am Eastern. Use the dashboard to edit it, add more newsletters, or send one immediately.

## Cost

- **Claude API:** ~$0.01–0.03 per newsletter → roughly $0.50–1.50/year per newsletter
- **Resend:** Free for up to 100 emails/month
- **GitHub Actions + Pages:** Free tier (more than sufficient)

## Project Structure

```
huginn/
├── index.html                             ← Web UI (hosted on GitHub Pages)
├── newsletter.py                          ← Generator + sender (run by GitHub Actions)
├── newsletters/
│   └── biosecurity.json                   ← One config file per newsletter
├── requirements.txt
├── .github/workflows/
│   └── newsletter-biosecurity.yml         ← One workflow per newsletter (auto-generated)
└── .gitignore
```
