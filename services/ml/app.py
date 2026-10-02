from fastapi import FastAPI

app = FastAPI(title="PetMatch ML placeholder", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok", "model": "not-configured"}
