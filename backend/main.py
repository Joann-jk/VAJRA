from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title="Multimodal Conversation Intelligence Backend",
    description="Backend service for the hackathon — analyzes conversations with Gemini and runs a simple risk engine.",
)

app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # hackathon mode
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)