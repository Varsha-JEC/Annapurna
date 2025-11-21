from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import os

from dotenv import load_dotenv
import google.generativeai as genai

import firebase_admin
from firebase_admin import credentials, firestore

# --------------------------------------------------------------------------
# --- ENV + FIREBASE INITIALIZATION ---
# --------------------------------------------------------------------------

# Load .env from project root (one level above backend/)
ENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(ENV_PATH, override=True)

# Initialize Firebase Admin SDK
def init_firestore():
    try:
        if not firebase_admin._apps:
            cred_path = os.getenv("FIREBASE_CREDENTIALS_JSON_PATH")
            if not cred_path or not os.path.exists(cred_path):
                raise RuntimeError(
                    "Firebase credentials file not found. "
                    "Check FIREBASE_CREDENTIALS_JSON_PATH in environment."
                )

            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase initialized successfully")

        return firestore.client()
    except Exception as e:
        print(f"❌ Firebase initialization error: {e}")
        return None

db = init_firestore()
if db is None:
    # We still start the server, but endpoints will raise 500 if DB is not ready
    print("⚠️ Firestore DB is NOT initialized. API calls will fail until fixed.")

# --------------------------------------------------------------------------
# --- GEMINI AI CONFIGURATION ---
# --------------------------------------------------------------------------

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

try:
    genai.configure(api_key=GEMINI_API_KEY)
    print("✅ Gemini API configured successfully")
except Exception as e:
    raise RuntimeError(f"Failed to configure Gemini API: {str(e)}")

# --------------------------------------------------------------------------
# --- FASTAPI APP + CORS ---
# --------------------------------------------------------------------------

app = FastAPI(
    title="Annapurna FoodBridge API",
    description="Backend services for handling donations and AI chat for the NGO portal.",
    version="1.0.0",
)

# TODO: Replace "*" with your exact Streamlit Cloud URL for better security
origins = [
    "*",
    # e.g. "https://annapurna-frontend.streamlit.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------
# --- Pydantic Data Models ---
# --------------------------------------------------------------------------

class ChatRequest(BaseModel):
    prompt: str = Field(..., example="How can I reduce food wastage at home?")

class ChatResponse(BaseModel):
    response: str


class NgoAcceptRequest(BaseModel):
    """Data that NGO sends when accepting a donation."""
    ngo_name: str = Field(..., example="Helping Hands Foundation")
    ngo_contact_email: str = Field(..., example="contact@helpinghands.org")


class DonationCreate(BaseModel):
    """
    Model for creating a new donation from any client (mobile/web).
    Matches your donor Streamlit code structure.
    """
    donor_name: str = Field(..., example="Jane's Bakery")
    donor_email: str = Field(..., example="donor@example.com")
    food_name: str = Field(..., example="Surplus Bread and Pastries")
    quantity: int = Field(..., example=30)
    food_type: str = Field(..., example="Veg")
    expiry_date: datetime = Field(..., example="2025-10-14T22:00:00Z")
    contact_number: str = Field(..., example="+91-9876543210")
    address: str = Field(..., example="Koramangala, Bengaluru")
    description: Optional[str] = Field(None, example="Fresh leftovers from today's batch")
    image_url: Optional[str] = Field(
        None,
        example="https://example.com/food-image.jpg"
    )


class DonationOut(BaseModel):
    """
    Model for donation as returned by the API.
    Uses Firestore document ID as string.
    """
    id: str
    donor_name: str
    donor_email: str
    food_name: str
    quantity: int
    food_type: str
    expiry_date: datetime
    contact_number: str
    address: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    accepted_by_ngo: Optional[str] = None
    accepted_by_email: Optional[str] = None
    accepted_at: Optional[datetime] = None


class DonationStats(BaseModel):
    """Model for dashboard statistics."""
    total_donations: int
    pending_donations: int
    accepted_donations: int

# --------------------------------------------------------------------------
# --- Helper Functions ---
# --------------------------------------------------------------------------

def ensure_db():
    """Ensure Firestore is initialized; otherwise raise server error."""
    if db is None:
        raise HTTPException(
            status_code=500,
            detail="Firestore database is not initialized on the server.",
        )
    return db

def firestore_ts_to_datetime(value):
    """Convert Firestore Timestamp to datetime, or pass through if already datetime/None."""
    if value is None:
        return None
    # Firestore Timestamp has .to_datetime()
    if hasattr(value, "to_datetime"):
        return value.to_datetime()
    if isinstance(value, datetime):
        return value
    return None


def donation_doc_to_model(doc) -> DonationOut:
    """Convert Firestore doc to DonationOut model."""
    data = doc.to_dict()
    return DonationOut(
        id=doc.id,
        donor_name=data.get("donor_name", ""),
        donor_email=data.get("donor_email", ""),
        food_name=data.get("food_name", ""),
        quantity=int(data.get("quantity", 0)),
        food_type=data.get("food_type", ""),
        expiry_date=firestore_ts_to_datetime(data.get("expiry_date")) or datetime.utcnow(),
        contact_number=data.get("contact_number", ""),
        address=data.get("address", ""),
        description=data.get("description"),
        image_url=data.get("image_url"),
        status=data.get("status", "Pending"),
        created_at=firestore_ts_to_datetime(data.get("created_at")),
        accepted_by_ngo=data.get("accepted_by_ngo"),
        accepted_by_email=data.get("accepted_by_email"),
        accepted_at=firestore_ts_to_datetime(data.get("accepted_at")),
    )

# --------------------------------------------------------------------------
# --- Root Endpoint ---
# --------------------------------------------------------------------------

@app.get("/")
def read_root():
    return {"message": "Annapurna FoodBridge Backend is running."}

# --------------------------------------------------------------------------
# --- CHAT ENDPOINT ---
# --------------------------------------------------------------------------

@app.post("/api/chat", response_model=ChatResponse, tags=["AI Chat"])
def chat_with_gemini(request: ChatRequest):
    """Receives a prompt and returns a response from the Gemini AI model."""
    try:
        model = genai.GenerativeModel("gemini-1.5-pro-latest")
        response = model.generate_content(request.prompt)
        return {"response": response.text}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error communicating with AI model: {str(e)}"
        )

# --------------------------------------------------------------------------
# --- DONATION ENDPOINTS (Firestore) ---
# --------------------------------------------------------------------------

@app.post(
    "/api/donations",
    response_model=DonationOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Donations"],
)
def create_donation(donation: DonationCreate):
    """
    Create a new donation in Firestore.
    This mirrors the data structure used in your Donor Streamlit app.
    """
    db = ensure_db()

    donation_data = {
        "donor_name": donation.donor_name.strip(),
        "donor_email": donation.donor_email.strip().lower(),
        "food_name": donation.food_name.strip(),
        "quantity": int(donation.quantity),
        "food_type": donation.food_type,
        "expiry_date": donation.expiry_date,
        "contact_number": donation.contact_number.strip(),
        "address": donation.address.strip(),
        "description": donation.description.strip() if donation.description else "",
        "image_url": donation.image_url,
        "status": "Pending",  # same as donor portal
        "created_at": firestore.SERVER_TIMESTAMP,
    }

    try:
        doc_ref = db.collection("donations").add(donation_data)[1]  # (write_result, reference)
        saved_doc = doc_ref.get()
        return donation_doc_to_model(saved_doc)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error saving donation to Firestore: {str(e)}"
        )


@app.get("/api/donations", response_model=List[DonationOut], tags=["Donations"])
def get_available_donations():
    """
    Returns all 'Pending' donations from Firestore.
    This is equivalent to your NGO portal's get_available_donations().
    """
    db = ensure_db()
    try:
        query = db.collection("donations").where("status", "==", "Pending").stream()
        donations = [donation_doc_to_model(doc) for doc in query]
        # Sort by created_at desc (if available)
        donations.sort(
            key=lambda d: d.created_at or datetime.min,
            reverse=True,
        )
        return donations
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching donations: {str(e)}"
        )


@app.put(
    "/api/donations/{donation_id}/accept",
    response_model=DonationOut,
    tags=["Donations"],
)
def accept_donation(donation_id: str, ngo_details: NgoAcceptRequest):
    """
    NGO accepts a donation.
    This updates the Firestore document exactly the same way
    as your Streamlit NGO accept_donation() function.
    """
    db = ensure_db()
    try:
        doc_ref = db.collection("donations").document(donation_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Donation not found."
            )

        data = doc.to_dict()
        current_status = data.get("status", "Pending")

        if current_status != "Pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Donation is already {current_status} and cannot be accepted.",
            )

        # Update status and NGO info
        doc_ref.update({
            "status": "Accepted",
            "accepted_by_ngo": ngo_details.ngo_name,
            "accepted_by_email": ngo_details.ngo_contact_email,
            "accepted_at": firestore.SERVER_TIMESTAMP,
        })

        updated_doc = doc_ref.get()
        return donation_doc_to_model(updated_doc)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error accepting donation: {str(e)}"
        )

# --------------------------------------------------------------------------
# --- STATS ENDPOINT ---
# --------------------------------------------------------------------------

@app.get("/api/donations/stats", response_model=DonationStats, tags=["Dashboard"])
def get_donation_stats():
    """
    Provides aggregated data about all donations.
    Uses simple in-memory counting over Firestore results.
    """
    db = ensure_db()
    try:
        docs = list(db.collection("donations").stream())
        total = len(docs)
        pending = 0
        accepted = 0

        for doc in docs:
            status_val = doc.to_dict().get("status", "Pending")
            if status_val == "Pending":
                pending += 1
            elif status_val == "Accepted":
                accepted += 1

        return DonationStats(
            total_donations=total,
            pending_donations=pending,
            accepted_donations=accepted,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating donation stats: {str(e)}"
        )
