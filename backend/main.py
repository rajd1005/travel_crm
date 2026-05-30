import hmac
import secrets
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, Header, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# Assuming database.py handles the SQLAlchemy engine and sessionmaker
# from database import SessionLocal, engine
# from models import Base, tcc_ensure_database_guards

app = FastAPI(title="Travel CRM Master API", version="1.0.0")

# CORS Setup - Allows your React frontend and WordPress child sites to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your specific child site domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from database import SessionLocal, init_db

# FastAPI startup event handler
@app.on_event("startup")
def on_startup():
    # Runs your custom DB guards and ensures tables are ready
    init_db()

# Update your get_db() dependency to use the real database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# --- Security: API Key Authentication Bridge ---
# You will store this securely in your SystemConfig table or .env file
MASTER_API_KEY = "sk_live_1234567890abcdef1234567890abcdef" 

def verify_api_key(x_tcc_api_key: str = Header(None)):
    """
    Timing-safe API key comparison. Prevents side-channel timing attacks
    by always taking the exact same amount of time to compare strings.
    """
    if not x_tcc_api_key:
        raise HTTPException(status_code=401, detail="Missing API Key Header")
    
    # hmac.compare_digest ensures strict security parity with WordPress's hash_equals
    if not hmac.compare_digest(x_tcc_api_key.encode("utf-8"), MASTER_API_KEY.encode("utf-8")):
        raise HTTPException(status_code=403, detail="Invalid API Key")
    
    return True

# --- Pydantic Models for Request Validation ---
class PartialLeadPayload(BaseModel):
    client_name: str
    client_phone: str
    client_email: Optional[str] = None
    tour_id: Optional[int] = None

class BookingPayload(BaseModel):
    tour_id: int
    date_selected: str
    pax_count: int
    client_name: str
    client_phone: str
    client_email: Optional[str] = None
    rooms: List[Dict[str, Any]]

# --- API Endpoints ---

@app.get("/api/v1/ping", dependencies=[Depends(verify_api_key)])
def ping_server(request: Request):
    """
    Connectivity test for the WordPress Child Plugin.
    We also log the IP/URL of the child site to track connections.
    """
    client_host = request.client.host
    # Here you would update SystemConfig.last_seen_timestamp in the DB
    return {"status": "success", "message": "Mother System Online", "child_ip": client_host, "timestamp": datetime.utcnow()}

@app.get("/api/v1/settings", dependencies=[Depends(verify_api_key)])
def get_global_settings():
    """
    Returns the Form Config (GST, Form Flow, WA Number) to the Child Site.
    """
    # Fetch from SystemConfig table
    return {
        "global_gst_percent": 5.00,
        "whatsapp_number": "+919876543210",
        "default_form_flow": "tour-select-first"
    }

@app.get("/api/v1/tours", dependencies=[Depends(verify_api_key)])
def get_published_tours(destination: Optional[str] = None):
    """
    Streams all published Fixed Departure tours with dates and pricing.
    """
    # Query FixedTour table, filter by destination if provided
    return {
        "tours": [
            {
                "id": 1,
                "title": "Kashmir Paradise Group Tour",
                "destination": "Kashmir",
                "days": 6,
                "next_departure": "2026-06-15",
                "starting_price": 24500,
                "live_seats_left": 12
            }
        ]
    }

@app.get("/api/v1/seats", dependencies=[Depends(verify_api_key)])
def get_live_seats():
    """
    Lightweight endpoint dedicated strictly to fetching the 'FOMO' seat counts.
    """
    return {
        "tour_1_date_2026-06-15": 12,
        "tour_1_date_2026-06-22": 4, # FOMO Trigger: "Only 4 seats left!"
    }

@app.post("/api/v1/leads/partial")
def capture_partial_lead(payload: PartialLeadPayload, background_tasks: BackgroundTasks):
    """
    Abandoned Form Capture. Fires immediately when user advances past Step 1.
    No API Key required here since it fires directly from the public frontend form.
    """
    # 1. Save to database as a 'Warm Lead'
    # 2. Fire background task to email admin
    
    def send_admin_alert(name, phone):
        # Email logic here (e.g., using smtplib or AWS SES)
        print(f"Alert: Captured warm lead - {name} ({phone})")
        
    background_tasks.add_task(send_admin_alert, payload.client_name, payload.client_phone)
    
    return {"status": "captured"}

@app.post("/api/v1/book", dependencies=[Depends(verify_api_key)])
def create_booking(payload: BookingPayload):
    """
    Master booking endpoint. Receives payload, saves to database, 
    calculates pricing, deducts live seats, and returns URLs.
    """
    # 1. Verify seat availability
    # 2. Generate unique Quote Slug (e.g., A7x9B2kQ)
    # 3. Calculate exact pricing using compute_financials() from pricing_engine.py
    # 4. Save to Quote JSONB column
    
    generated_slug = "A7x9B2kQ"
    quote_url = f"https://yourdomain.com/quote/{generated_slug}"
    
    # Generate WhatsApp URL
    wa_message = f"Hello {payload.client_name}, your booking for {payload.pax_count} pax is confirmed! View invoice: {quote_url}"
    wa_encoded = wa_message.replace(" ", "%20")
    wa_redirect_url = f"https://wa.me/919876543210?text={wa_encoded}"

    return {
        "status": "success",
        "quote_slug": generated_slug,
        "quote_url": quote_url,
        "whatsapp_redirect": wa_redirect_url
    }
