
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import SessionLocal, Property, Lead

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Models for API
class ChatMessage(BaseModel):
    text: str
    phone: str

class LeadUpdate(BaseModel):
    phone: str
    budget: str = None
    goal: str = None

# Seed database with properties
def seed_db():
    db = SessionLocal()
    if db.query(Property).count() == 0:
        properties = [
            Property(title="Penthouse Vista Mar", price_eur=748000, location="Leblon", meta="3 BR • 220m²", description="Vista oceânica deslumbrante."),
            Property(title="Loft Industrial", price_eur=141000, location="Pinheiros", meta="1 BR • 65m²", description="Estilo moderno e alta rentabilidade."),
            Property(title="Reserva do Vale", price_eur=1290000, location="Amarante", meta="12 Hectares", is_off_market=True, description="O ápice da privacidade e luxo rural."),
        ]
        db.add_all(properties)
        db.commit()
    db.close()

seed_db()

@app.post("/chat")
async def chat_endpoint(msg: ChatMessage, db: Session = Depends(get_db)):
    # Logic to mimic Marco Rossi
    text = msg.text.lower()
    phone = msg.phone
    
    lead = db.query(Lead).filter(Lead.phone == phone).first()
    if not lead:
        lead = Lead(phone=phone)
        db.add(lead)
        db.commit()

    # Simple State Machine for Qualification
    if "reserva do vale" in text or "off-market" in text:
        if not lead.is_qualified:
            return {"response": "A 'Reserva do Vale' é um ativo exclusivo. Para liberar o dossiê, preciso de 3 respostas rápidas: Qual seu objetivo, seu budget e seu prazo?"}
        return {"response": "Como você já está qualificado, aqui está o acesso ao Dossiê da Reserva do Vale: [Link PDF]. Deseja agendar a visita?"}

    if "budget" in text or "valor" in text or "euro" in text:
        lead.is_qualified = True
        db.commit()
        return {"response": "Perfil validado. Agora você tem acesso às nossas oportunidades Off-Market. O que mais deseja saber?"}

    return {"response": "Olá, sou o Marco Rossi. Estou aqui para encontrar o imóvel ideal para você. O que busca hoje?"}

@app.get("/properties")
async def get_properties(db: Session = Depends(get_db)):
    # Only return public properties by default
    return db.query(Property).filter(Property.is_off_market == False).all()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
