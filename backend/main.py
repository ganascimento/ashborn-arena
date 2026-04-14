from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import battle_router, builds_router, ws_router

app = FastAPI(title="Ashborn Arena")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(builds_router)
app.include_router(battle_router)
app.include_router(ws_router)


@app.get("/health")
def health():
    return {"status": "ok"}
