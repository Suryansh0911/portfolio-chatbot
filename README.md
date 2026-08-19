# 🚀 AI Portfolio Assistant

An interactive, AI-powered portfolio and resume assistant that allows recruiters and visitors to chat with a virtual version of me (Suryansh Gupta). This project features a modern Next.js chat interface powered by an advanced Retrieval-Augmented Generation (RAG) FastAPI backend.

## ✨ Key Features

### 🖥️ Frontend (Next.js & Vercel AI SDK)
- **Responsive Chat Interface:** Clean, modern, right-aligned message bubbles with a slide-out sidebar for mobile.
- **Local Memory:** Chat history is seamlessly persisted in the browser's `localStorage`.
- **Markdown & Code Rendering:** Fully parses and renders markdown formatting for AI responses.
- **Dynamic Resume Uploads:** Integrated UI to upload a new resume, automatically rebuilding the backend vector database.
- **Typing Indicators:** Animated, native-feeling typing states for API requests.

### ⚙️ Backend (Python, FastAPI & Qdrant)
- **Advanced RAG Pipeline:** Context-aware semantic search using Qdrant vector database.
- **Compound Question Decomposition:** Automatically breaks down complex, multi-part questions into individual queries.
- **Intent Classification:** Routes queries dynamically (e.g., factual retrieval vs. multi-role candidate evaluation).
- **Evidence Verification & Grounding:** Built-in safeguards to prevent AI hallucinations, explicitly correcting false premises from users.
- **Streaming Responses:** Real-time token streaming for a fast, responsive user experience.
- **Containerized:** Ready for scalable deployment on AWS via Docker.

---

## 🏗️ Architecture

- **Frontend Hosting:** Vercel
- **Backend API:** AWS EC2 (Dockerized FastAPI)
- **Vector Database:** Qdrant
- **LLM Provider:** Groq (Configurable via Environment Variables)

---

## 🚀 Getting Started

### Prerequisites
- Node.js 18+
- Python 3.11+
- Docker (Optional, for backend deployment)
- API Keys: Qdrant, Groq (or your chosen LLM provider)

### 1. Backend Setup (FastAPI)

Navigate to the backend directory and install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

Set up your `.env` file:
```env
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_key
GROQ_API_KEY=your_groq_key
```

Run the FastAPI server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

*(Alternatively, run via Docker)*
```bash
docker build -t portfolio-backend .
docker run -d -p 8000:8000 --env-file .env portfolio-backend
```

### 2. Frontend Setup (Next.js)

Navigate to the frontend directory:
```bash
cd frontend
npm install
```

Set up your `.env.local` file:
```env
# Point this to your local or AWS backend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Start the development server:
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to view the application in your browser.

---

## 🔄 Updating the Resume
You can update the portfolio's knowledge base on the fly:
1. Open the sidebar in the frontend UI.
2. Click **Upload New Resume**.
3. Select your updated PDF/TXT file. 
4. The system will automatically overwrite the old data, wipe the Qdrant collection, generate new embeddings, and rebuild the vector store.

---

## 🛡️ License
This project is open-source and available under the [MIT License](LICENSE).