import os
import logging
from datetime import datetime
from typing import Optional, Tuple, Dict, Any, List

import googlemaps

# Optional Streamlit support
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GoogleMapsService:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Google Maps client."""
        self.api_key = api_key or os.getenv("GOOGLE_MAPS_API_KEY")
        if not self.api_key:
            raise ValueError("Google Maps API key is required")

        self.client = googlemaps.Client(key=self.api_key)

    def handle_error(self, message: str, exception: Exception):
        """Handle errors for both Streamlit and non-Streamlit use."""
        full_msg = f"{message}: {str(exception)}"
        if STREAMLIT_AVAILABLE:
            st.error(full_msg)
        else:
            logger.error(full_msg)

    # --- Geocode Address ---
    def geocode_address(self, address: str) -> Optional[Dict[str, Any]]:
        """Convert an address to latitude and longitude."""
        try:
            geocode_result = self.client.geocode(address)
            if geocode_result and len(geocode_result) > 0:
                result = geocode_result[0]
                return {
                    'formatted_address': result.get('formatted_address'),
                    'location': result['geometry']['location'],
                    'place_id': result.get('place_id')
                }
            return None
        except Exception as e:
            self.handle_error("Error geocoding address", e)
            return None

    # --- Get Nearby NGOs ---
    def get_nearby_ngos(
        self,
        location: Tuple[float, float],
        radius: int = 5000,
        keyword: str = "NGO"
    ) -> List[Dict]:
        """Find NGOs near a specific location."""
        try:
            places_result = self.client.places_nearby(
                location=location,
                radius=radius,
                keyword=keyword
            )
            return places_result.get('results', [])
        except Exception as e:
            self.handle_error("Error finding nearby NGOs", e)
            return []

    # --- Get Directions ---
    def get_directions(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        mode: str = "driving"
    ) -> Optional[Dict]:
        """Get directions between two points."""
        try:
            now = datetime.now()
            directions_result = self.client.directions(
                origin=origin,
                destination=destination,
                mode=mode,
                departure_time=now
            )
            return directions_result[0] if directions_result else None
        except Exception as e:
            self.handle_error("Error getting directions", e)
            return None
