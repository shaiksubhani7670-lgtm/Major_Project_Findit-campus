# FindIt Campus — Deployment Guide

This document describes how to deploy **FindIt Campus** to production services: Next.js frontend to **Vercel**, and Flask API backend with PostgreSQL, Redis, and Celery worker to **Render**.

---

## Frontend Deployment (Vercel)

Vercel provides native Next.js deployment.

1. Create a Vercel project linked to your repository.
2. In **Build & Development Settings**, keep default settings.
3. Configure the following **Environment Variables**:
   - `NEXT_PUBLIC_API_URL`: `https://your-backend-url.onrender.com/api`
   - `NEXT_PUBLIC_APP_NAME`: `FindIt Campus`
4. Click **Deploy**.

---

## Backend Deployment (Render)

Render can run web servers, background workers, and PostgreSQL/Redis instances.

### 1. PostgreSQL Database
- Click **New** → **PostgreSQL**.
- Choose a name and tier.
- Render automatically generates a internal/external connection URL.

### 2. Redis Instance
- Click **New** → **Redis**.
- Render generates a internal connection URL (e.g., `redis://red-xxx:6379`).

### 3. Flask API Service
- Click **New** → **Web Service**.
- Select the `backend` folder as the root directory.
- Configure **Build Command**: `pip install -r requirements.txt`
- Configure **Start Command**: `gunicorn run:app`
- Add the following **Environment Variables**:
  - `FLASK_ENV`: `production`
  - `SECRET_KEY`: `<secure-random-key>`
  - `DATABASE_URL`: `postgresql://...` (from Render PostgreSQL)
  - `REDIS_URL`: `redis://...` (from Render Redis)
  - `JWT_SECRET_KEY`: `<secure-random-key>`
  - `CLOUDINARY_CLOUD_NAME`: `your-cloudinary-name`
  - `CLOUDINARY_API_KEY`: `your-cloudinary-key`
  - `CLOUDINARY_API_SECRET`: `your-cloudinary-secret`
  - `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER`

### 4. Celery Worker (Background Job Runner)
- Click **New** → **Background Worker**.
- Set root directory to `backend`.
- Configure **Build Command**: `pip install -r requirements.txt`
- Configure **Start Command**: `celery -A app.tasks.matching_tasks worker --loglevel=info`
- Set the same environment variables as the Flask API.
