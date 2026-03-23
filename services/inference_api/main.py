cat > services/inference_api/main.py << 'EOF'
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/signals/latest")
def latest(h: str = "30m"):
    return {
        "status": "ok",
        "note": "THIS IS NEW CODE",
        "horizon": h
    }
EOF
