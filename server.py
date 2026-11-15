import json
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from main import app as graph_app 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # In a real app with logins, this would be the user's actual account ID
    config = {"configurable": {"thread_id": "demo_user_1"}}
    
    async def event_generator():
        # Notice we added config=config here to connect to the SQLite memory!
        async for event in graph_app.astream_events({"messages": [request.message]}, config=config, version="v2"):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"].content
                if chunk and isinstance(chunk, str):
                    # Format as a Server-Sent Event (SSE)
                    yield f"data: {json.dumps({'text': chunk})}\n\n"
        
        # Signal to the React frontend that the stream is finished
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")