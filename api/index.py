from fastapi import FastAPI

app = FastAPI(
    title="Synthetic User Generation Platform",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "name": "Synthetic User Generation Platform",
        "status": "online",
        "message": "API is running successfully",
    }


@app.get("/api")
def api_root():
    return {
        "name": "Synthetic User Generation Platform",
        "status": "online",
    }


@app.get("/api/health")
def health():
    return {
        "status": "ok",
    }