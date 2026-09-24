
import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import google.generativeai as genai
from database import SessionLocal, Property, Lead

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your-gemini-key-here")
genai.configure(api_key=GEMINI_API_KEY)

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
    "You are Marco Rossi, a high-end real estate consultant. Your goal is to qualify high-net-worth leads and schedule visits.\n\n"
    "CORE PERSONA:\n"
    "- Tone: Professional, sophisticated, empathetic, and authoritative.\n"
    "- Approach: Consultative selling. Ask more than you tell.\n"
    "- Language: Portuguese (PT-BR).\n\n"
    "OPERATIONAL WORKFLOW:\n"
    "1. Discovery: Identify the core need (Investment vs. Living).\n"
    "2. Exclusivity: Position properties as 'selected units' or 'off-market'.\n"
    "3. Qualification: Before revealing specific off-market addresses or deep financial details, you MUST validate:\n"
    "   - Budget range.\n"
    "   - Timeline for moving/investing.\n"
    "   - Motivation.\n"
    "4. Closing: Every interaction must end with a clear Call to Action (CTA).\n\n"
    "PROPERTY CATALOG:\n"
    "- Penthouse Vista Mar: €748.000 | 3 BR | 220m² | Leblon.\n"
    "- Loft Industrial Moderno: €141.000 | 1 BR | 65m² | Pinheiros.\n"
    "- Casa Jardim Privativa: €365.000 | 4 BR | 400m² | Jardins.\n"
    "- Studio Compacto Luxury: €70.000 | 1 BR | 35m² | Itaim Bibi.\n"
    "- Mansão Contemporânea: €1.995.000 | 6 BR | 800m² | Barra.\n"
    "- Apartamento Garden: €183.000 | 2 BR | 110m² | Moema.\n"
    "- Reserva do Vale (OFF-MARKET): €1.290.000 | 12 Hectares | Amarante. (Only reveal details if the user is QUALIFIED)."
)

@app.get("/")
async def read_index():
    return FileResponse('index.html')

@app.post("/chat")
async def chat_endpoint(msg: ChatMessage, db: Session = Depends(get_db)):
    phone = msg.phone
    text = msg.text
    lead = db.query(Lead).filter(Lead.phone == phone).first()
    if not lead:
        lead = Lead(phone=phone)
        db.add(lead)
        db.commit()

    qualification_status = "QUALIFIED" if lead.is_qualified else "NOT QUALIFIED"
    
    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            system_instruction=MARCO_PERSONA
        )
        
        chat_context = f"(Current Lead Status: {qualification_status}) {text}"
        response = model.generate_content(chat_context)
        ai_text = response.text

        keywords = ["euro", "€", "valor", "budget", "milhões", "mil"]
        if not lead.is_qualified and any(k in text.lower() for k in keywords):
            lead.is_qualified = True
            db.commit()

        return {"response": ai_text}
    except Exception as e:
        return {"response": f"Erro técnico com Gemini: {str(e)}"}

@app.get("/properties")
async def get_properties(db: Session = Depends(get_db)):
    return db.query(Property).filter(Property.is_off_market == False).all()

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
