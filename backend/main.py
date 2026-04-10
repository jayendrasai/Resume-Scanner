# from fastapi import FastAPI, UploadFile, File, HTTPException
# import fitz  # PyMuPDF
# import io

from fastapi import FastAPI, UploadFile, File,Form ,  HTTPException , Request
import fitz
import io
import os
import json
from groq import Groq
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import requests

load_dotenv()
#load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
# Initialize Groq Client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

HF_API_KEY = os.getenv("HF_API_KEY")

print("KEY:", os.getenv("GROQ_API_KEY"))

# Initialize Rate Limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# def call_huggingface(prompt):
#     API_URL = "https://router.huggingface.co/v1/chat/completions"

#     headers = {
#         "Authorization": f"Bearer {HF_API_KEY}",
#         "Content-Type": "application/json"
#     }

#     payload = {
#         "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
#         "messages": [
#             {
#                 "role": "system",
#                 "content": "You are a recruitment expert. Return ONLY JSON with keys: match_score, missing_keywords, tips"
#             },
#             {
#                 "role": "user",
#                 "content": prompt
#             }
#         ],
#         "max_tokens": 500,
#         "temperature": 0.2
#     }

#     response = requests.post(API_URL, headers=headers, json=payload)

#     data = response.json()
#     print("HF RAW RESPONSE:", data)

#     # Safe extraction
#     if "choices" in data:
#         return data["choices"][0]["message"]["content"]

#     # fallback format
#     if "generated_text" in data:
#         return data["generated_text"]

#     # fallback list format
#     if isinstance(data, list):
#         return data[0].get("generated_text", str(data))

#     return str(data)
#     data = response.json()

#     #return data["choices"][0]["message"]["content"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allows all origins
    #allow_credentials=True,
    allow_methods=["POST"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

@app.post("/analyze")
@limiter.limit("3/minute")
async def analyze_resume(
    request: Request,
    file: UploadFile = File(...), 
    job_description: str = Form(...)
):
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
        #sda
        if not resume_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF.")
        

        # --- Placeholder for Day 2: OpenAI Logic ---
        # 2. AI Logic (Groq)
        try:
            completion = client.chat.completions.create(
                
                model="llama-3.3-70b-versatileqqq",
                messages=[
                    {"role": "system", "content": "You are a recruitment expert. Compare the resume to the JD. Return ONLY a JSON object with keys: 'match_score', 'missing_keywords', and 'tips'."},
                    {"role": "user", "content": f"JD: {job_description}\n\nResume: {resume_text}"}
                ],
                response_format={"type": "json_object"}
            )
            print("Text from groq: ",completion.choices[0].message.content)
            return json.loads(completion.choices[0].message.content)

        except Exception as e:
            print("Groq failed → switching to HuggingFace")

            prompt = f"""
            Return ONLY JSON:

            JD:
            {job_description}

            Resume:
            {resume_text}

            Format:
            {{
            "match_score": number,
            "missing_keywords": [],
            "tips": []
            }}
            """

            hf_response = call_huggingface(prompt)
            print("Text from huggingface: ",hf_response)
            return hf_response

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

