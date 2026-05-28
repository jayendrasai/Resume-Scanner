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
from services.ai import analyze_resume_with_ai, analyze_transcript_with_ai
from payments.router import router as payments_router




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

app.include_router(auth_router)
app.include_router(storage_router)
app.include_router(jobs_router)
app.include_router(payments_router)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)



app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze")
async def analyze_resume(
    request: Request,
    file: UploadFile = File(...), 
    job_description: str = Form(...),
    #guest_id: str = Depends(verify_guest_id)
):
    # --------for docker --------
    guest_id = request.headers.get("X-Guest-ID")
    ip = get_real_ip(request)

    # --------for local --------
    #guest_id = request.headers.get("X-Guest-ID")
    #ip = request.client.host

    count = get_user_scan_count(guest_id, ip)

    if count >= 3:
        raise HTTPException(
            status_code=429,
            detail="Limit reached. Try again after 3 hours."
        )

    log_activity(guest_id, ip, file.filename)

    # 1. Validation
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    try:
        # 2. In-Memory Extraction
        pdf_content = await file.read()
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        resume_text = ""
        for page in doc:
            resume_text += page.get_text()

        # 3. Validation of content
        if not resume_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF.")

        return analyze_resume_with_ai(job_description, resume_text)

    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/extract-text")
async def extract_text(file: UploadFile = File(...)):
    # Validate file type
    if file.content_type != "application/pdf":
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
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


@app.get("/premium-test")
async def premium_test(user=Depends(require_premium)):
    return {"ok": True}

@app.get("/history")
async def get_my_history(request: Request):
    guest_id = request.headers.get("X-Guest-ID")

    all_history = get_history()
    # Filter only for THIS user
    user_history = [h for h in all_history if h['guest_id'] == guest_id]
    return user_history

@app.get("/healthz")
def health():
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

