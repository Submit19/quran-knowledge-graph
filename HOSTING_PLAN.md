# Hosting Plan — Publishing the Quran Knowledge Graph UI

## Overview

Deploy the Quran Knowledge Graph as a public website with 5 pages:
1. `/` — Chat interface + 3D verse graph (requires Neo4j + Anthropic API)
2. `/stats` — Statistical dashboard
3. `/deductions` — 3D meta-knowledge graph + deduction insights
4. `/visualizations` — Interactive Chart.js dashboard
5. `/presentation` — Reveal.js slide deck

## Architecture Options

### Option A: Static Export (Easiest, Free)
**Best for: Deductions, Visualizations, Presentation pages**

These pages can work as static HTML with pre-baked data (no server needed).

1. Bundle the JSON data directly into the HTML files
2. Host on **GitHub Pages**, **Netlify**, or **Vercel** (all free)
3. No backend needed — all data is embedded

**Steps:**
```bash
# Create a static build
mkdir -p dist
# Inline the JSON data into each HTML file
python3 scripts/build_static.py
# Deploy to GitHub Pages
git subtree push --prefix dist origin gh-pages
```

**Pros**: Free, fast, zero maintenance
**Cons**: No live chat, no real-time deduction updates

---

### Option B: Full Stack on Railway/Render (Recommended)
**Best for: Full experience including chat**

Deploy the FastAPI app with all features.

**Services needed:**
1. **Web server**: FastAPI + uvicorn (the app.py we already have)
2. **Neo4j**: Neo4j Aura Free Tier (cloud graph database)
3. **Anthropic API**: Your existing API key

**Platform: Railway.app** (recommended)
- Free tier: 500 hours/month
- Easy Python deployment
- Environment variables for secrets

**Steps:**
```bash
# 1. Create requirements.txt
pip freeze > requirements.txt

# 2. Create Procfile
echo "web: uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}" > Procfile

# 3. Create railway.toml
cat > railway.toml << 'EOF'
[build]
builder = "nixpacks"

[deploy]
startCommand = "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}"
healthcheckPath = "/api/deductions/status"
EOF

# 4. Deploy
railway login
railway init
railway up
```

**Environment variables to set:**
```
ANTHROPIC_API_KEY=sk-ant-...
NEO4J_URI=neo4j+s://xxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=...
NEO4J_DATABASE=quran
```

**Cost**: ~$0-5/month (Railway free tier + Neo4j Aura free)

---

### Option C: Docker Compose (Self-hosted)
**Best for: Full control, run on your own server**

```yaml
# docker-compose.yml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8080:8080"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=${NEO4J_PASSWORD}
    depends_on:
      - neo4j

  neo4j:
    image: neo4j:5-community
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}
    volumes:
      - neo4j_data:/data

volumes:
  neo4j_data:
```

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_sm
COPY . .
EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
```

**Deploy to**: DigitalOcean ($5/mo droplet), AWS EC2, Google Cloud Run, or any VPS.

---

### Option D: Hybrid (Best Balance)
**Static pages on GitHub Pages + API on Railway**

1. Deploy the 4 static pages (deductions, visualizations, presentation, stats) to GitHub Pages (free)
2. Deploy the FastAPI backend to Railway for the chat + live API endpoints
3. Configure CORS on the API to allow the static site to call it

This gives you:
- Free hosting for the data-heavy pages
- Paid (cheap) hosting only for the interactive chat
- Easy to update static content by pushing to GitHub

---

## Recommended Path

### Phase 1: Immediate (Today)
1. **GitHub Pages** for static pages
2. Create `build_static.py` script to embed JSON data into HTML
3. Push to `gh-pages` branch

### Phase 2: This Week
1. Sign up for **Neo4j Aura** free tier
2. Import graph data (`import_neo4j.py`)
3. Deploy FastAPI to **Railway** free tier
4. Connect chat to the cloud Neo4j

### Phase 3: Growth
1. Custom domain (e.g., quran-graph.com)
2. Add authentication for the chat (rate limiting)
3. Set up the continuous runner as a background worker
4. Add a feedback system for users to rate deduction quality

## Files to Create for Deployment

```
requirements.txt     — pip dependencies
Procfile            — process command for Railway/Heroku
Dockerfile          — container build
docker-compose.yml  — full stack with Neo4j
railway.toml        — Railway config
.github/workflows/deploy.yml — CI/CD pipeline
scripts/build_static.py — static site builder
```

## Quick Start: Static Export

The fastest way to get something live:

```bash
# Build static versions with embedded data
python3 scripts/build_static.py

# Preview locally
python3 -m http.server 8000 --directory dist

# Deploy to GitHub Pages
git checkout -b gh-pages
cp dist/* .
git add -A
git commit -m "Deploy static site"
git push origin gh-pages
```

The site will be live at: `https://alikatkodia-collab.github.io/quran-knowledge-graph/`
