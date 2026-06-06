# ## AI Resume Scanner
This is a production-grade, containerized full-stack platform designed to provide instant, high-fidelity feedback on resumes using Large Language Models. Engineered with a **Stateless Hybrid Security** model, the system balances user privacy with robust rate limiting and high-speed inference.

## ## Features
* **High-Performance AI Inference:** Leverages **Groq Cloud (Llama-3.3-70b)** for near-instantaneous analysis with a sub-500ms response time.
* **Resilient Waterfall Pipeline:** Implements an **OpenRouter Fallback** mechanism to iterate through secondary models (Gemma, Qwen, etc.) if the primary provider fails.
* **Hybrid Security & Rate Limiting:** Enforces a 3-hour sliding window limit using a dual-layer check of **Guest-IDs** and **Client IP addresses**.
* **Concurrency-Safe Ledger:** Utilizes a flat-file JSON history manager hardened with **Unix fcntl file locking** to prevent data corruption during simultaneous writes.
* **Enterprise UI/UX:** Features a modular React frontend with **Skeleton Loaders**, real-time **Scanning Animations**, and instant **PDF Export** capabilities.

---

## ## System Architecture
The platform follows a decoupled, two-container architecture optimized for cloud scalability.

### ### Component Strategy
* **Nginx Reverse Proxy:** Acts as a unified entry point, serving static React assets and proxying `/api` requests to the backend to eliminate CORS overhead.
* **FastAPI Backend:** A stateless service that performs in-memory PDF parsing using **PyMuPDF**, ensuring no user resumes are ever stored on disk.
* **Persistence Layer:** A Docker-mounted volume for `history.json` that tracks anonymized usage metrics across container restarts.

---

## ## Getting Started

### ### Prerequisites
* Docker and Docker Compose
* Groq API Key and/or OpenRouter API Key

### ### Installation & Deployment
1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/jayendrasaichenna/resume-scanner.git]
    cd resume-scanner
    ```
2.  **Configure Environment:**
    Create a `.env` file in the root directory:
    ```env
    GROQ_API_KEY=your_key_here
    OPENROUTER_API_KEY=your_key_here
    JWT_SECRET=your_secret_here
    ```
3.  **Launch Service:**
    ```bash
    docker-compose up --build -d
    ```
The application will be available at `http://localhost:80` (via Nginx).

---

## ## API Documentation
The backend provides interactive Swagger UI documentation at `http://localhost:8000/docs`.

### ### Primary Endpoints
| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/health` | `GET` | Returns 200 OK when service and AI providers are reachable. |
| `/analyze` | `POST` | Processes a PDF resume against a Job Description string. Requires `X-Guest-ID` header. |
| `/history` | `GET` | Retrieves the last 5 scans for the current Guest ID. |

---

## ## Design Decisions & Strategy
* **Privacy-First Parsing:** Resumes are read into RAM as byte streams and discarded immediately after inference to maintain a stateless footprint.
* **Proxy-Aware IP Tracking:** The backend utilizes the `X-Forwarded-For` header to accurately identify client IPs when deployed behind cloud load balancers.
* **Regex-Based Extraction:** Since LLMs can produce noisy outputs, the system uses a custom Regex parser to safely extract valid JSON objects from raw markdown blocks.
* **Concurrency Handling:** To support multi-worker Uvicorn environments, `fcntl.flock` provides exclusive write access to the history ledger.
