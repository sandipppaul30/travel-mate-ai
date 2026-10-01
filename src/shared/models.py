
from pydantic import BaseModel, Field

class FlightResponse(BaseModel):
    flight_details: str = Field(..., description="Details about the flight, including departure and arrival airports, airlines, duration, airfare range, peak season pricing, and booking advice.")