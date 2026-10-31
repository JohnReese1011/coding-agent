from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn
from coding_agent.graph import CodingTeam
from coding_agent.settings import API_HOST, API_PORT

team = CodingTeam()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await team.build()
    yield

app = FastAPI(title="Local Coding Agent API", version="0.1.0", lifespan=lifespan)

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20000)
    thread_id: str = "default"

class ApprovalRequest(BaseModel):
    decision: str
    thread_id: str = "default"

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        return {"thread_id": req.thread_id, **(await team.ainvoke(req.message, req.thread_id))}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"{type(exc).__name__}: {exc}")

@app.post("/approval")
async def approval(req: ApprovalRequest):
    if req.decision not in {"approve", "reject"}:
        raise HTTPException(status_code=400, detail="decision must be approve or reject")
    try:
        return {"thread_id": req.thread_id, **(await team.resume(req.decision, req.thread_id))}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"{type(exc).__name__}: {exc}")

def run():
    uvicorn.run("coding_agent.api:app", host=API_HOST, port=API_PORT, reload=False)
