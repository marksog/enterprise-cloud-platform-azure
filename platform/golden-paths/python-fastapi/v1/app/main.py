from fastapi import FastAPI

app = FastAPI(title="SOG Platform Application")


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/ready")
def ready():
    return {"status": "ready"}


@app.get("/")
def root():
    return {"message": "Deployed through SOG Developer Platform"}
