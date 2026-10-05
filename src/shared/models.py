
from pydantic import BaseModel, Field

class FlightResponse(BaseModel):
    flight_details: str = Field(..., description="Details about the flight, including departure and arrival airports, airlines, duration, airfare range, peak season pricing, and booking advice.")

class HotelResponse(BaseModel):
    hotel_details: str = Field(..., description="Details about the hotel, including location, amenities, pricing, and booking advice.")

class WeatherResponse(BaseModel):
    weather_details: str = Field(..., description="Details about the weather, including current conditions, temperature, humidity, wind speed, and forecast.")

class Destination(BaseModel):
    name: str = Field(..., description="The name of the destination.")

class BudgetResponse(BaseModel):
    budget_details: str = Field(..., description="Details about the budget, including estimated costs for flights, hotels, meals, activities, and any additional expenses.")

class ItineraryResponse(BaseModel):
    itinerary_details: str = Field(..., description="Details about the itinerary, including a day-by-day plan, activities, and recommendations.")

class TripConstraints(BaseModel):
    destination: str = Field(..., description="The destination for the trip.")
    origin: str = Field(..., description="The origin of the trip.")
    duration: str = Field(..., description="The duration of the trip.")
    budget: str = Field(..., description="The budget for the trip.")
    travel_style: str = Field(..., description="The travel style for the trip (e.g., luxury, budget, adventure).")
    special_preferences: list[str] = Field(..., description="Any special preferences for the trip (e.g., dietary restrictions, accessibility needs).")

class SupervisorResponse(BaseModel):
    selected_agents: list[str] = Field(..., description="List of selected agents for the task.")
    trip_constraints: TripConstraints = Field(..., description="Constraints for the trip, including destination, origin, duration, budget, travel style, and special preferences.")
    reasoning: str = Field(..., description="Reasoning behind the selection of agents and trip constraints.")