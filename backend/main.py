# from fastapi import FastAPI, UploadFile, File, HTTPException
# import fitz  # PyMuPDF
# import io

from fastapi import FastAPI, UploadFile, File,Form ,  HTTPException , Request , Depends
import fitz
import io
import os
import json
import re
from groq import Groq
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import requests
from openai import OpenAI
from auth.router import router as auth_router
from database import Base, engine
from auth.dependencies import require_premium
from storage.router import router as storage_router
from jobs_router import router as jobs_router
from services.ai import analyze_resume_with_ai, analyze_transcript_with_ai , sanitize_llm_input,MAX_JD_LENGTH,MAX_RESUME_LENGTH
from payments.router import router as payments_router
from logger import log
from database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from history_manager import get_user_scan_count, log_activity, get_history




#from middleware import verify_guest_id
from history_manager import log_activity, get_user_scan_count , get_history
from middleware import get_real_ip


load_dotenv()
#load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
# Initialize Groq Client
#client = Groq(api_key=os.getenv("GROQ_API_KEY"))

#OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# New OpenRouter Fallback Client
# openrouter_client = OpenAI(
#     base_url="https://openrouter.ai/api/v1",
#     api_key=OPENROUTER_API_KEY,
# )

# Initialize Rate Limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# app.include_router(auth_router)
# app.include_router(storage_router)
# app.include_router(jobs_router)
# app.include_router(payments_router)
# main.py — update all router mounts:
app.include_router(auth_router,     prefix="/v1")
app.include_router(storage_router,  prefix="/v1")
app.include_router(jobs_router,     prefix="/v1")
app.include_router(payments_router, prefix="/v1")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://172.18.0.6:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET" , "POST"],
    allow_headers=["Content-Type", "Authorization", "X-Guest-ID","X-Idempotency-Key"],
)


# main.py — replace PDF validation block
async def validate_pdf_magic_bytes(file: UploadFile) -> bytes:
    """
    PDF magic number: first 4 bytes must be %PDF
    Validates actual file content, not just extension.
    """
    pdf_content = await file.read()
    if not pdf_content[:4] == b'%PDF':
        log.error("Invalid file. Only PDF files are accepted.")
        raise HTTPException(
            status_code=400,
            detail="Invalid file. Only PDF files are accepted."
        )

    # Size check — 5MB
    if len(pdf_content) > 5 * 1024 * 1024:
        log.error("File too large. Maximum size is 5 MB.")
        raise HTTPException(
            status_code=413,
            detail="File too large. Maximum size is 5 MB."
        )
    return pdf_content

@app.post("/v1/analyze")
async def analyze_resume(
    request: Request,
    file: UploadFile = File(...), 
    job_description: str = Form(...),
    #guest_id: str = Depends(verify_guest_id)
    db: AsyncSession = Depends(get_db)
):
    
    SCAN_LIMIT = 3
    # --------for docker --------
    guest_id = request.headers.get("X-Guest-ID")
    ip = get_real_ip(request)
    log.info("User IP", ip=ip, guest_id=guest_id)
    # --------for local --------
    #guest_id = request.headers.get("X-Guest-ID")
    #ip = request.client.host

    count = await get_user_scan_count(db, guest_id, ip)
    log.info("User Scan Count", guest_id=guest_id, ip=ip, count=count)

    if count >= SCAN_LIMIT:
        log.error("Limit reached. Try again after 2 hours.")
        raise HTTPException(
            status_code=429,
            detail="Limit reached. Try again after 2 hours."
        )

    await log_activity(db, guest_id, ip, file.filename)

    pdf_content = await validate_pdf_magic_bytes(file)

    # 1. Validation
    # if not file.filename.endswith('.pdf'):
    #     raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    try:
        # 2. In-Memory Extraction
        #pdf_content = await file.read()
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        resume_text = ""
        for page in doc:
            resume_text += page.get_text()

        # 3. Validation of content
        if not resume_text.strip():
            log.error("Could not extract text from PDF.")
            raise HTTPException(status_code=400, detail="Could not extract text from PDF.")
        
        # After PDF extraction, before AI call:
        try:
            job_description = sanitize_llm_input(
                job_description, MAX_JD_LENGTH, "Job description"
            )
            resume_text = sanitize_llm_input(
                resume_text, MAX_RESUME_LENGTH, "Resume"
            )
        except ValueError as e:
            log.error("Invalid input", error=str(e))
            raise HTTPException(status_code=400, detail=str(e))
        log.info("Sanitized Input")
        return analyze_resume_with_ai(job_description, resume_text)

    except Exception as e:
        log.error("Unexpected Error", error=str(e))
        return {"status": "error", "message": str(e)}

@app.post("/v1/extract-text")
async def extract_text(file: UploadFile = File(...)):
    # Validate file type
    if file.content_type != "application/pdf":
        log.error("Invalid file. Only PDF files are accepted.")
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        # Read file into memory
        contents = await file.read()
        doc = fitz.open(stream=contents, filetype="pdf")
        
        full_text = ""
        for page in doc:
            full_text += page.get_text()
            
        return {"filename": file.filename, "text": full_text}
    
    except Exception as e:
        log.error("Error processing PDF", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


@app.get("/v1/premium-test")
async def premium_test(user=Depends(require_premium)):
    return {"ok": True}

@app.get("/v1/history")
async def get_my_history(request: Request,db:AsyncSession = Depends(get_db)):
    guest_id = request.headers.get("X-Guest-ID")
    if not guest_id:
        log.error("Guest ID not found")
        raise HTTPException(status_code=400, detail="Guest ID not found")
    history = await get_history(db, guest_id)
    return history

@app.get("/healthz")
def health():
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

