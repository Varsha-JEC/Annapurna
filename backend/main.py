from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import uuid4, UUID
from datetime import datetime
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="Annapurna FoodBridge API",
    description="Backend services for handling donations and AI chat for the NGO portal.",
    version="1.0.0"
)

# --------------------------------------------------------------------------
# --- GEMINI AI CONFIGURATION ---
# --------------------------------------------------------------------------

# Get API key from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

# Configure Gemini API
try:
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    raise RuntimeError(f"Failed to configure Gemini API: {str(e)}")


# --------------------------------------------------------------------------
# --- IN-MEMORY DATABASE (Replace with Firebase/SQL in Production) ---
# --------------------------------------------------------------------------

# This is a temporary, in-memory list to store donations.
# Every time the server restarts, this data will be gone.
# TODO: Replace this with calls to your Firebase Firestore database.
DB_DONATIONS = [
    {
        "id": UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479"),
        "donorName": "John's Restaurant",
        "foodName": "Fresh Vegetable Curry",
        "quantity": "Serves 20",
        "location": "MG Road, Bengaluru",
        "expiryDate": "2025-10-15T18:00:00Z",
        "status": "Available",
        "createdAt": datetime.utcnow(),
        "acceptedByNgo": None
    },
    {
        "id": UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8"),
        "donorName": "Community Kitchen",
        "foodName": "Rice and Dal",
        "quantity": "Serves 50",
        "location": "Whitefield, Bengaluru",
        "expiryDate": "2025-10-14T12:00:00Z",
        "status": "Available",
        "createdAt": datetime.utcnow(),
        "acceptedByNgo": None
    }
]

# --------------------------------------------------------------------------
# --- Pydantic Data Models ---
# --------------------------------------------------------------------------

class ChatRequest(BaseModel):
    prompt: str

class ChatResponse(BaseModel):
    response: str

class NgoAcceptRequest(BaseModel):
    """Model for the data an NGO sends when accepting a donation."""
    ngo_name: str = Field(..., example="Helping Hands Foundation")
    ngo_contact_email: str = Field(..., example="contact@helpinghands.org")

class DonationCreate(BaseModel):
    """Model for creating a new donation. ID and status are set automatically."""
    donorName: str = Field(..., example="Jane's Bakery")
    foodName: str = Field(..., example="Surplus Bread and Pastries")
    quantity: str = Field(..., example="Approx. 30 items")
    location: str = Field(..., example="Koramangala, Bengaluru")
    expiryDate: datetime = Field(..., example="2025-10-14T22:00:00Z")

class DonationOut(BaseModel):
    """Model for representing a donation when sent to the client."""
    id: UUID
    donorName: str
    foodName: str
    quantity: str
    location: str
    expiryDate: datetime
    status: str
    createdAt: datetime
    acceptedByNgo: Optional[str]

class DonationStats(BaseModel):
    """Model for the dashboard visuals data."""
    total_donations: int
    available_donations: int
    accepted_donations: int


# --------------------------------------------------------------------------
# --- API Endpoints ---
# --------------------------------------------------------------------------

@app.get("/")
def read_root():
    return {"message": "Annapurna FoodBridge Backend is running."}


# --- CHAT ENDPOINT ---

@app.post("/api/chat", response_model=ChatResponse, tags=["AI Chat"])
def chat_with_gemini(request: ChatRequest):
    """Receives a prompt and returns a response from the Gemini AI model."""
    try:
        # CORRECTED: Using a valid, current model name
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        response = model.generate_content(request.prompt)
        return {"response": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with AI model: {str(e)}")


# --- DONATION ENDPOINTS ---

@app.post("/api/donations", response_model=DonationOut, status_code=status.HTTP_201_CREATED, tags=["Donations"])
def create_donation(donation: DonationCreate):
    """
    Endpoint for donors to register a new food donation.
    The new donation is automatically marked as 'Available'.
    """
    new_donation = donation.model_dump()
    new_donation.update({
        "id": uuid4(),
        "status": "Available",
        "createdAt": datetime.utcnow(),
        "acceptedByNgo": None
    })
    DB_DONATIONS.append(new_donation)
    return new_donation


@app.get("/api/donations", response_model=List[DonationOut], tags=["Donations"])
def get_available_donations():
    """
    Returns a list of all donations that are currently in 'Available' status.
    This is the main endpoint for NGOs to find food.
    """
    available = [d for d in DB_DONATIONS if d["status"] == "Available"]
    return available


@app.put("/api/donations/{donation_id}/accept", response_model=DonationOut, tags=["Donations"])
def accept_donation(donation_id: UUID, ngo_details: NgoAcceptRequest):
    """
    Allows an NGO to accept a donation. This changes its status from 'Available' to 'Accepted'.
    """
    for donation in DB_DONATIONS:
        if donation["id"] == donation_id:
            if donation["status"] != "Available":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Donation is already {donation['status']} and cannot be accepted."
                )
            
            donation["status"] = "Accepted"
            donation["acceptedByNgo"] = ngo_details.ngo_name
            return donation
            
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donation not found.")


# --- VISUALS/STATS ENDPOINT ---

@app.get("/api/donations/stats", response_model=DonationStats, tags=["Dashboard"])
def get_donation_stats():
    """
    Provides aggregated data about all donations, perfect for a statistics dashboard.
    """
    total = len(DB_DONATIONS)
    available = len([d for d in DB_DONATIONS if d["status"] == "Available"])
    accepted = len([d for d in DB_DONATIONS if d["status"] == "Accepted"])

    return {
        "total_donations": total,
        "available_donations": available,
        "accepted_donations": accepted
    }