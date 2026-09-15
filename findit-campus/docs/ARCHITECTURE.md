# FindIt Campus — System Architecture

FindIt Campus uses a modular, decoupled microservices-ready monolithic architecture designed for scalability, low latency, and high accuracy.

---

## Architecture Flowchart

```mermaid
flowchart TD
    subgraph Frontend [Next.js 15 App Router]
        UI[Framer Motion/Tailwind UI]
        APIClient[Axios Client]
    end

    subgraph Backend [Flask REST API]
        Controller[Flask Blueprints]
        Auth[JWT Handler]
        Models[SQLAlchemy Models]
        Services[Matching & Notification Services]
    end

    subgraph ML Pipeline [AI/ML Engine]
        YOLO[YOLOv8 Object Detector]
        OpenCV[Feature Extractor]
        HSV[Color Detector]
        OCR[EasyOCR Reader]
        Transformers[Sentence Transformer]
        FAISS[FAISS Vector Store]
    end

    subgraph Storage [Data Layer]
        DB[(PostgreSQL Database)]
        Redis[(Redis Cache & Broker)]
        Cloudinary[Cloudinary Cloud Storage]
    end

    subgraph Async Workers [Celery Tasks]
        Worker[Celery Worker]
    end

    %% Interactions
    UI -->|HTTPS/REST| APIClient
    APIClient -->|Requests| Controller
    Controller -->|Verify Tokens| Auth
    Controller -->|ORM Operations| Models
    Models --> DB
    
    %% File upload
    Controller -->|Cloud Upload| Cloudinary
    
    %% Celery workflow
    Controller -->|Dispatch Task| Redis
    Redis -->|Poll Tasks| Worker
    Worker -->|Execute Pipeline| Services
    Services -->|Run Inference| YOLO
    Services -->|Run OCR| OCR
    Services -->|Semantic Match| Transformers
    Services -->|Vector Search| FAISS
    Services -->|Write Matches| Models
