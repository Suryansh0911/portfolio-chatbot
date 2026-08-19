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
import os
import shutil

app = FastAPI(
    title = "Portfolio AI Chatbot",
    description="AI chatbot for Suryansh Gupta's professional protfolio",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Change this to your specific Vercel URL later
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
    x_admin_secret: str = Header(None)):
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized: Incorrect admin password.")

    try:
        file_location = f"data/resume.pdf" 
        os.makedirs(os.path.dirname(file_location), exist_ok=True)

        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)

        build_vector_store()

        return {"message": "Resume updated and vector store rebuilt successfully!"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))