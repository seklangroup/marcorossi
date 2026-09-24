import os
import requests
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import SessionLocal, Property, Lead

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ChatMessage(BaseModel):
    text: str
    phone: str

MARCO_PERSONA = (
    "You are Marco Rossi, a high-end real estate consultant. Qualify high-net-worth leads.\n"
    "Tone: Professional, sophisticated. Language: Portuguese (PT-BR).\n"
    "Workflow: 1. Discovery, 2. Exclusivity, 3. Qualification (Budget, Timeline), 4. Closing CTA.\n"
    "Catalog: Penthouse Vista Mar (€748k), Loft Industrial (€141k), Casa Jardim (€365k), Studio Luxury (€70k), Mansão Barra (€1.995M), Apartamento Garden (€183k), Reserva do Vale (€1.29M - OFF MARKET)."
)

@app.get("/")
async def read_index():
    return FileResponse('index.html')

@app.post("/chat")
async def chat_endpoint(msg: ChatMessage, db: Session = Depends(get_db)):
    if not GEMINI_API_KEY:
        return {"response": "Erro: GEMINI_API_KEY não configurada no Railway."}
    
    # Model fallback list: (API version, model name)
    attempts = [
        ("v1", "gemini-1.5-flash"),
        ("v1beta", "gemini-1.5-flash"),
        ("v1", "gemini-pro"),
        ("v1beta", "gemini-pro"),
    ]
    
    for version, model in attempts:
        url = f"https://generativelanguage.googleapis.com/v1{version if version != 'v1' else ''}/models/{model}:generateContent?key={GEMINI_API_KEY}"
        # Correction: the v1 URL is actually https://generativelanguage.googleapis.com/v1/models/...
        # If version is 'v1', it should be /v1/. If 'v1beta', it should be /v1beta/.
        
        # Re-constructing URL correctly
        fixed_url = f"https://generativelanguage.googleapis.com/{version}/models/{model}:generateContent?key={GEMINI_API_KEY}"
        
        payload = {"contents": [{"parts": [{"text": f"SYSTEM: {MARCO_PERSONA}\nUSER: {msg.text}"}]}]}
        
        try:
            response = requests.post(fixed_url, json=payload, timeout=7)
            if response.status_code == 200:
                data = response.json()
                return {"response": data['candidates'][0]['content']['parts'][0]['text']}
        except Exception:
            continue

    # If all attempts fail, let's try to list the available models for the user's key
    try:
        list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
        list_res = requests.get(list_url, timeout=5)
        if list_res.status_code == 200:
            models = [m['name'] for m in list_res.json().get('models', [])]
            return {"response": f"Erro de Modelo. Sua chave suporta: {', '.join(models[:5])}..."}
        return {"response": f"Erro na API Google: {list_res.status_code}"}
    except Exception as e:
        return {"response": f"Erro fatal: {str(e)}"}

@app.get("/properties")
async def get_properties(db: Session = Depends(get_db)):
    return db.query(Property).filter(Property.is_off_market == False).all()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
