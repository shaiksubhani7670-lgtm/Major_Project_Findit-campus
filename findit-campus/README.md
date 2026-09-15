# FindIt Campus — AI-Powered Smart Lost & Found System

FindIt Campus is a complete production-quality, AI-powered lost and found management system for colleges. Designed to significantly reduce recovery times, the system lets students report lost items, security staff privately log found items, and uses a multi-signal AI engine to automatically notify matches.

---

## Features

- **🎨 Premium UI/UX:** Responsive Next.js 15 layout using Tailwind CSS, Framer Motion, and Outfit/Inter typography.
- **🤖 AI Matching Engine:** Combines object detection (YOLOv8), semantic text similarity (Sentence Transformers), visual feature analysis (OpenCV), color classification (HSV), and text/identifiers extraction (EasyOCR).
- **🔒 Privacy First:** Found items logged by staff are never visible publicly to students. Only verified high-confidence matches trigger notifications.
- **📊 Analytics Dashboard:** Charts, trends, lost categories breakdown, location hotspots, and system performance health metrics.
- **⚡ Async Processing:** Celery + Redis background tasks for image analysis and notification dispatching.

---

## Project Structure

```
findit-campus/
├── frontend/          # Next.js 15 + React 19 + TypeScript
├── backend/           # Flask + SQLAlchemy + Celery
├── ml/                # AI/ML matching pipeline
│   ├── training/      # Training scripts
│   ├── models/        # Saved models
│   ├── datasets/      # Sample data
│   └── inference/     # Inference scripts
├── database/          # SQL schema, migrations, seed data
├── docs/              # Documentation, ER diagrams, flowcharts
├── docker-compose.yml
├── Dockerfile.frontend
└── Dockerfile.backend
```

---

## Setup & Running

### Requirements
- Docker and Docker Compose
- Cloudinary account (for image uploads)
- SMTP Server details (for email alerts)

### Running with Docker Compose

1. Copy `.env.example` to `.env` in the root:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and fill in Cloudinary & email service credentials.
3. Start the entire application:
   ```bash
   docker-compose up --build
   ```
4. Access the services:
   - **Frontend:** [http://localhost:3000](http://localhost:3000)
   - **Backend API:** [http://localhost:5000](http://localhost:5000)

### Manual Setup (Development)

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## Documentation Links

- [🚀 Architecture & Workflows](file:///c:/Users/harsh/OneDrive/Desktop/final%20year%20project/findit-campus/docs/ARCHITECTURE.md)
- [📦 Database ER Schema](file:///c:/Users/harsh/OneDrive/Desktop/final%20year%20project/findit-campus/docs/DATABASE.md)
- [🔗 API Reference & Endpoints](file:///c:/Users/harsh/OneDrive/Desktop/final%20year%20project/findit-campus/docs/API.md)
- [🛠️ Deployment Guide](file:///c:/Users/harsh/OneDrive/Desktop/final%20year%20project/findit-campus/docs/DEPLOYMENT.md)
