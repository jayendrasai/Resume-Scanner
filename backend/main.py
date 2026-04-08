# from fastapi import FastAPI, UploadFile, File, HTTPException
# import fitz  # PyMuPDF
# import io

from fastapi import FastAPI, UploadFile, File,Form ,  HTTPException
import fitz
import io
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    #allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

@app.post("/analyze")
async def analyze_resume(
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
        if not resume_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF.")

        # --- Placeholder for Day 2: OpenAI Logic ---
        # result = call_openai(resume_text, job_description)
        
        return {
            "status": "success",
            "extracted_length": len(resume_text),
            "job_desc_preview": job_description[:50] + "...",
            "message": "Text extracted successfully. Ready for AI analysis."
        }

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