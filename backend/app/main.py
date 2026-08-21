from fastapi import FastAPI, HTTPException, UploadFile, File, Header
from app.services.parser import parse_resume
from app.models.schemas import Portfolio, ChatMessage, ChatRequest, ChatResponse
from app.services.chatbot import chat
from app.services.portfolio import load_portfolio
from app.services.memory import get_history, add_message, clear_history
from fastapi.responses import StreamingResponse
from app.services.chatbot import chat, stream_chat
from fastapi.middleware.cors import CORSMiddleware
from app.rag.vector_store import build_vector_store
from app.rag.resume_converter import resume_text_to_portfolio
import os
import shutil
import json

app = FastAPI(
    title = "Portfolio AI Chatbot",
    description="AI chatbot for Suryansh Gupta's professional protfolio",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://portfolio-chatbot-suryansh.vercel.app",
                    "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")

def root():
    return {
        "message": "Portfolio Chatbot is running"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }

@app.get("/resume")
def get_resume():
    resume_path = "data/resume.pdf"

    try:
        text = parse_resume(resume_path)
        return {
        "file_name": resume_path, 
        "text": text,
        "characters": len(text)
        }

    except Exception as e:
        raise HTTPException(
            status_code = 500, 
            detail = str(e)
        )

@app.get("/portfolio")
def get_portfolio():

    try:
        portfolio = load_portfolio()

        return portfolio

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.post("/chat", response_model=ChatResponse)
def chat_with_portfolio(request: ChatRequest):

    try:

        history = get_history(
            request.conversation_id
        )

        response = chat(
            request.message,
            history
        )

        add_message(
            request.conversation_id,
            "user",
            request.message
        )

        add_message(
            request.conversation_id,
            "assistant",
            response
        )

        return ChatResponse(
            conversation_id=request.conversation_id,
            response=response
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.delete("/chat/{conversation_id}")
def delete_conversation(conversation_id: str):

    clear_history(conversation_id)

    return {
        "message": "Conversation history cleared",
        "conversation_id": conversation_id
    }

@app.post("/chat/stream")
def stream_chat_with_portfolio(
    request: ChatRequest
):

    history = get_history(
        request.conversation_id
    )

    def event_stream():

        full_response = ""

        for chunk in stream_chat(
            request.message,
            history
        ):

            full_response += chunk

            yield chunk

        add_message(
            request.conversation_id,
            "user",
            request.message
        )

        add_message(
            request.conversation_id,
            "assistant",
            full_response
        )

    return StreamingResponse(
        event_stream(),
        media_type="text/plain"
    )


ADMIN_SECRET = os.getenv("ADMIN_SECRET", "my_super_secret_password")

@app.post("/api/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    x_admin_secret: str = Header(None),
):
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized: Incorrect admin password.")

    try:
        # 1. Save the uploaded file, preserving its real extension
        extension = os.path.splitext(file.filename)[1].lower()
        if extension not in (".pdf", ".docx"):
            raise HTTPException(status_code=400, detail="Only PDF or DOCX files are supported.")

        file_location = f"data/resume{extension}"
        os.makedirs(os.path.dirname(file_location), exist_ok=True)

        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)

        print(f"[upload] File written to {file_location}, size: {os.path.getsize(file_location)} bytes")

        # 2. Extract raw text
        raw_text = parse_resume(file_location)
        print(f"[upload] Extracted {len(raw_text)} chars of text")

        # 3. Convert to structured Portfolio via Groq
        portfolio = resume_text_to_portfolio(raw_text)
        print(f"[upload] Parsed portfolio: {portfolio.personal.name}, "
              f"{len(portfolio.experience)} experience entries, "
              f"{len(portfolio.projects)} projects")

        # 4. Overwrite portfolio.json with the new structured data
        with open("data/portfolio.json", "w", encoding="utf-8") as f:
            json.dump(portfolio.model_dump(), f, indent=2, ensure_ascii=False)

        # 5. Rebuild the vector store from the freshly written portfolio.json
        build_vector_store()

        return {"message": "Resume updated and vector store rebuilt successfully!"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))