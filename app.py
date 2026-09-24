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
MARCO_PERSONA = "You are Marco Rossi, a luxury real estate agent. Speak Portuguese (PT-BR). Focus on high-net-worth qualification."
@app.get("/")
async def read_index():
    return FileResponse('index.html')
@app.post("/chat")
async def chat_endpoint(msg: ChatMessage, db: Session = Depends(get_db)):
    if not GEMINI_API_KEY:
        return {"response": "Erro: GEMINI_API_KEY não configurada."}
    
    url = f"https://generativelanguage.googleapis.com/v1beta/interactions"
    payload = {
        "model": "gemini-3.8-flash",
        "input": f"SYSTEM: {MARCO_PERSONA}\nUSER: {msg.text}"
    }
    headers = {"x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            # PROCURA INTELIGENTE: Percorre os steps até encontrar a resposta do modelo
            for step in data.get('steps', []):
                if step.get('type') == 'model_output':
                    contents = step.get('content', [])
                    for item in contents:
                        if item.get('type') == 'text':
                            return {"response": item.get('text')}
            
            return {"response": "O Marco Rossi pensou na resposta, mas não conseguiu escrevê-la. Tente novamente."}
        
        return {"response": f"Erro API Interações: {response.status_code} - {response.text}"}
    except Exception as e:
        return {"response": f"Erro de Conexão: {str(e)}"}
@app.get("/properties")
async def get_properties(db: Session = Depends(get_db)):
    return db.query(Property).filter(Property.is_off_market == False).all()
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
