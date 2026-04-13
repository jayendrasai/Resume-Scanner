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



#from middleware import verify_guest_id
from history_manager import log_activity, get_user_scan_count , get_history
from middleware import get_real_ip


load_dotenv()
#load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
# Initialize Groq Client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# New OpenRouter Fallback Client
openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Initialize Rate Limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def parse_llm_json(text: str):
    try:
        return json.loads(text)
    except:
        # extract JSON block
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("No JSON found")

        cleaned = match.group(0)

        # remove control characters
        cleaned = cleaned.replace("\n", " ")
        cleaned = cleaned.replace("\t", " ")

        return json.loads(cleaned)

def call_openrouter_fallback(system_prompt: str, job_description: str, resume_text: str):
    print("Initiating OpenRouter Fallback Waterfall...")
    
    # Priority list of free models
    fallback_models = [
        "google/gemma-4-31b-it:free",
        "nvidia/nemotron-3-super-120b-a12b:free",
        "minimax/minimax-m2.5:free",
        "qwen/qwen3-coder:free",
        "nvidia/nemotron-3-nano-30b-a3b:free"
    ]

    for model_name in fallback_models:
        print(f"Attempting inference with: {model_name}")
        try:
            completion = openrouter_client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "http://localhost:8000", # Replace with your app URL
                    "X-Title": "Resume AI Scanner",
                },
                model=model_name, 
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"JD: {job_description}\n\nResume: {resume_text}"}
                ],
                # response_format={"type": "json_object"}, # Kept disabled for free model compatibility
                temperature=0.1,
                max_tokens=1000
            )
            
            # Safety Check: Ensure 'choices' actually exists
            if getattr(completion, 'choices', None) is None or len(completion.choices) == 0:
                raise ValueError("API returned an empty choices list.")
     
            fallback_response = completion.choices[0].message.content
            
            if not fallback_response:
                 raise ValueError("API returned empty message content.")
                 
            print(f"Success with {model_name}!")
            
            # If parsing succeeds, return the data and EXIT the function
            return parse_llm_json(fallback_response)
            
        except Exception as e:
            # Catch the error, print it, and the loop will naturally try the next model
            print(f"Model {model_name} failed: {e}. Moving to next fallback...")
            continue

    # If the loop finishes and EVERY model failed, hit the final safety net
    print("All fallback models exhausted. Returning default error state.")
    return {
        "match_score": 0,
        "missing_keywords": ["API Error: Could not analyze"],
        "tips": ["Please try again later. All AI services are currently experiencing high traffic or downtime."]
    }


# def call_openrouter_fallback(system_prompt: str, job_description: str, resume_text: str):
#     print("Initiating OpenRouter Fallback...")
#     try:
#         completion = openrouter_client.chat.completions.create(
#             extra_headers={
#                 "HTTP-Referer": "http://localhost:8000", # Replace with your app URL
#                 "X-Title": "Resume AI Scanner",
#             },
#             # Using a reliable, free-tier model on OpenRouter
#             model="google/gemma-4-31b-it:free", 
#             messages=[
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user", "content": f"JD: {job_description}\n\nResume: {resume_text}"}
#             ],
#             #response_format={"type": "json_object"},
#             temperature=0.1,
#             max_tokens=1000
#         )
#         # Safety Check: Ensure 'choices' actually exists before subscripting
#         if getattr(completion, 'choices', None) is None or len(completion.choices) == 0:
#             raise ValueError("API returned an empty choices list.")
 
#         fallback_response = completion.choices[0].message.content
#         print("Text from OpenRouter: ", fallback_response)
#         return parse_llm_json(fallback_response)
        
        
#     except Exception as e:
#         print(f"OpenRouter Fallback also failed: {e}")
#         # Final safety net if both APIs are completely down
#         return {
#             "match_score": 0,
#             "missing_keywords": ["API Error: Could not analyze"],
#             "tips": ["Please try again later. Both primary and fallback AI services are currently unavailable."]
#         }


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["POST" , "GET"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    #allow_headers=["*"],  # Allows all headers
    allow_headers=["Content-Type", "X-Guest-ID"]
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
    print("from docker Guest------:", guest_id)
    print("from docker IP--------:", ip)



    # --------for local --------
    #guest_id = request.headers.get("X-Guest-ID")
    #ip = request.client.host

    count = get_user_scan_count(guest_id, ip)

    if count >= 8:
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
        #sda
        if not resume_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF.")
        

        # --- Placeholder for Day 2: OpenAI Logic ---
        # 2. AI Logic (Groq)
        try:
            # Updated System Prompt
            system_prompt = """
                    You are a Senior Technical Recruiter and ATS Optimization Expert. 
                    Your task is to conduct a high-fidelity GAP analysis between a Job Description (JD) and a Resume.

                    CRITICAL INSTRUCTIONS:
                    1. SCORING RUBRIC: Calculate a single overall match score from 0 to 100. Weigh your calculation based on:
                    - Hard Skills (50%): Tech stack, tools, platforms.
                    - Experience (30%): Relevance of past roles.
                    - Soft Skills/Education (20%): Leadership, degrees.
                    2. MISSING KEYWORDS: Identify specific technical terms present in the JD but missing from the resume.
                    3. TIPS: Provide exactly 5 actionable suggestions. These MUST be plain text strings. Do NOT use nested objects for tips.
                    4. FORMAT: Return ONLY a valid JSON object exactly matching the schema below.

                    EXPECTED JSON SCHEMA:
                    {
                    "match_score": <integer between 0 and 100>,
                    "missing_keywords": ["keyword1", "keyword2", "keyword3"],
                    "tips": ["string1", "string2", "string3", "string4", "string5"]
                    }
                """
            completion = client.chat.completions.create(
                
                model="llama-3.3-70b-versatileqqqq",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"JD: {job_description}\n\nResume: {resume_text}"}
                ],
                response_format={"type": "json_object"}
            )
            print("Text from groq: ",completion.choices[0].message.content)
            return json.loads(completion.choices[0].message.content)

        except Exception as e:

            print(f"Groq failed ({e}) → switching to OpenRouter Fallback")
            
            # 2. Fallback AI (OpenRouter Llama 8B Free)
            # We pass the EXACT same system prompt so the JSON schema matches perfectly
            return call_openrouter_fallback(system_prompt, job_description, resume_text)

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

