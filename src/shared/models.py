
from pydantic import BaseModel, Field

class FlightResponse(BaseModel):
    flight_details: str = Field(..., description="Details about the flight, including departure and arrival airports, airlines, duration, airfare range, peak season pricing, and booking advice.")

class HotelResponse(BaseModel):
    hotel_details: str = Field(..., description="Details about the hotel, including location, amenities, pricing, and booking advice.")

class WeatherResponse(BaseModel):
    weather_details: str = Field(..., description="Details about the weather, including current conditions, temperature, humidity, wind speed, and forecast.")

class Destination(BaseModel):
    name: str = Field(..., description="The name of the destination.")