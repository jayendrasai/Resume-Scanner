# AI Resume Scanner

**Live Demo:** [scanneraudit.work.gd](https://scanneraudit.work.gd)[cite: 3]
**Author:** Jayendra Sai Chenna

## Executive Summary
AI Resume Scanner is a production-ready SaaS platform built in 10 days (Phase 1 & Phase 2) that provides instant AI-driven feedback on resumes and interview communication skills. 

The system features two core workflows:
* **Resume Parsing:** Upload a PDF resume and paste a job description to receive structured AI feedback in under 3 seconds[cite: 3].
* **Interview Analysis:** Record an interview which is uploaded to AWS S3, processed via FFmpeg and Whisper, and analyzed by an LLM for communication metrics[cite: 3].

 ## User Roles & Premium Features

The application implements a strict, tiered authorization model to securely gate advanced features and manage infrastructure costs:

* **Guest (Anonymous Trial):** Allowed to use the PDF resume scanner, but restricted by a dual-layer rate limit (IP address + UUID sliding window) of 3 scans per 3 hours.
* **Registered (Free Tier):** Authenticated via JWT, allowing users to safely log in and maintain a history of their scans. 
* **Premium (Paid SaaS Tier):** Unlocked via a Razorpay 30-day pass. Premium users gain exclusive access to the asynchronous AI Video Interview Analysis feature.
* **Strict Route Protection:** All S3 video upload and Celery job execution endpoints (`/v1/upload/*` and `/v1/jobs/*`) are strictly gated behind a custom `require_premium` backend middleware.
* **Smart Expiration Logic:** The authentication system handles subscription expiration by validating the pass time-to-live *before* checking the user's tier. This ensures the frontend gracefully gates expired users without throwing incorrect or confusing token errors.

## Tech Stack
### Frontend
* **Core:** React 18+, TypeScript, Vite.
* **Components & UI:** Recharts for filler word bar charts, SVG-based pace gauges, and a responsive dropzone interface.
  

### Backend & AI
* **Framework:** Python 3.12, FastAPI[cite: 3].
* **AI/ML:** Groq Cloud (Llama 3.3-70b-versatile, Whisper-large-v3), OpenRouter for an LLM fallback waterfall[cite: 3].
* **Processing Tools:** PyMuPDF (fitz) for PDF extraction, FFmpeg for extracting 16kHz mono WAV files from video[cite: 3].

### Infrastructure & DevOps
* **Cloud Provider:** AWS (EC2 t3.small, RDS PostgreSQL 16, S3 for object storage)[cite: 3].
* **Containerization:** 5-container Docker Compose production stack[cite: 3].
* **Web Server:** Nginx as a reverse proxy with Let's Encrypt / Certbot for automatic TLSv1.2+ SSL renewal[cite: 3].
* **Message Broker:** Redis 7 and Celery[cite: 3].

## System Architecture
The application runs in an isolated EC2 Docker private network[cite: 3]. 
* Incoming traffic hits an Nginx reverse proxy on ports 80/443[cite: 3].
* Nginx routes internal traffic to the FastAPI backend running on port 8000[cite: 3].
* Background tasks (like video analysis) are offloaded to a Celery worker via Redis[cite: 3]. 
* State and scan histories are persisted in an AWS RDS PostgreSQL database located in a private subnet, reachable only from the EC2 security group[cite: 3].

## Security & Idempotency
Security and fault tolerance are foundational to this architecture.
* **Payment Idempotency:** Integrating Razorpay webhooks utilizes a dual-boundary idempotency system[cite: 3]. It leverages `Redis SET NX` to acquire worker locks and set a processing state, entirely preventing race conditions and replay attacks[cite: 3].
* **Identity & Access Management:** Implements JWT authentication with `HS256` signed tokens containing `jti` and `iat` claims to prevent identical tokens from being issued within the same second[cite: 3]. Passwords are encrypted using `bcrypt` via `passlib` with a work factor of 12[cite: 3].
* **Input Validation:** Enforces server-side limits of 5MB for PDFs and 100MB for videos[cite: 3]. PDF authenticity is verified by checking that the first 4 magic bytes match `%PDF` to reject renamed executables[cite: 3].
* **Cloud Security:** AWS S3 uploads are strictly handled via short-lived Presigned PUT URLs with server-generated object keys to prevent client-side path traversal[cite: 3].

## Core API Reference

| Method | Endpoint | Auth | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/v1/auth/register` | None | Register returns JWT[cite: 3] |
| `POST` | `/v1/analyze` | Guest-ID | PDF resume analysis - rate limited[cite: 3] |
| `POST` | `/v1/upload/presign` | Premium | Get S3 presigned PUT URL[cite: 3] |
| `POST` | `/v1/jobs/create` | Premium | Enqueue video analysis Celery task[cite: 3] |
| `GET` | `/v1/jobs/{task_id}/status` | Premium | Poll job status and result[cite: 3] |
| `POST` | `/v1/webhooks/razorpay` | HMAC-Sig | `order.paid` handler - Idempotent[cite: 3] |

## Local Development Setup

This project uses Docker Compose for a streamlined local development experience. The development environment spins up the React frontend, FastAPI backend, Celery worker, Redis, and a local PostgreSQL database.

### Prerequisites
* [Docker](https://docs.docker.com/get-docker/) and Docker Compose installed on your machine.
* Git



### Steps:


Step 1: Clone the Repository
```bash
git clone [https://github.com/jayendrasai/Resume-Scanner.git](https://github.com/jayendrasai/Resume-Scanner.git)
cd Resume-Scanner
````
Step 2: Environment Configuration
You need to set up your environment variables before running the application.

Navigate to the backend directory.

Copy the example environment file to create your local .env file:

```Bash
   cp backend/.env.example backend/.env
```
Open backend/.env and fill in your external API keys:

Groq API Key: Required for Llama 3.3 and Whisper AI analysis.

AWS Credentials: Required for S3 video uploads (Access Key, Secret Key, Region, Bucket Name).

Razorpay Keys: Required for testing the payment gateway.

JWT Secret: A secure random string for signing auth tokens.

(Note: Repeat this process in the frontend folder if it contains a .env.example file).

Step 3: Build and Run with Docker Compose
To start the entire application stack using the development configuration, run:

```Bash
docker-compose -f docker-compose.dev.yml up --build
```
Step 4: Run Database Migrations
Once the containers are up and the PostgreSQL database is running, apply the Alembic migrations to create the required tables (users, payments, guest_scans)[cite: 3]:

```Bash
# Run this in a new terminal window
docker-compose -f docker-compose.dev.yml exec backend alembic upgrade head
```
Step 5: Access the Application
With the containers running successfully, you can access the local services at the following URLs:

React Frontend (Vite): http://localhost:5173

[cite: 3]

FastAPI Backend / Swagger Docs: http://localhost:8000/docs

[cite: 3]

Redis Broker: localhost:6379

PostgreSQL Database: localhost:5432

Stopping the Services
To stop the local environment and remove the containers, press Ctrl+C in the terminal where Docker is running, or run:

```Bash
docker-compose -f docker-compose.dev.yml down
```
