from fastapi import FastAPI

app = FastAPI(title="Ashborn Arena")


@app.get("/health")
def health():
    return {"status": "ok"}
