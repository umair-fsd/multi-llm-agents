"""Weather tool using OpenWeatherMap API."""

import logging
from typing import Optional

import httpx

from src.config import OPENWEATHERMAP_API_KEY

logger = logging.getLogger(__name__)


class WeatherTool:
    """Get current weather and forecasts using OpenWeatherMap API."""
    
    def __init__(self):
        self.api_key = OPENWEATHERMAP_API_KEY
        self.base_url = "https://api.openweathermap.org/data/2.5"
    
    async def get_current_weather(self, city: str, units: str = "metric") -> dict:
        """
        Get current weather for a city.
        
        Args:
            city: City name (e.g., "London", "New York, US")
            units: "metric" (Celsius), "imperial" (Fahrenheit), or "standard" (Kelvin)
            
        Returns:
            Weather data dict or error dict
        """
        if not self.api_key:
            return {"error": "OpenWeatherMap API key not configured"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/weather",
                    params={
                        "q": city,
                        "appid": self.api_key,
                        "units": units,
                    },
                    timeout=10.0,
                )
                
                if response.status_code == 404:
                    return {"error": f"City '{city}' not found"}
                
                response.raise_for_status()
                data = response.json()
                
                return {
                    "city": data["name"],
                    "country": data["sys"]["country"],
                    "temperature": data["main"]["temp"],
                    "feels_like": data["main"]["feels_like"],
                    "humidity": data["main"]["humidity"],
                    "description": data["weather"][0]["description"],
                    "wind_speed": data["wind"]["speed"],
                    "units": units,
                }
                
        except httpx.HTTPError as e:
            logger.error(f"Weather API error: {e}")
            return {"error": f"Failed to get weather: {str(e)}"}
    
    async def get_forecast(self, city: str, units: str = "metric") -> dict:
        """
        Get 5-day weather forecast for a city.
        
        Args:
            city: City name
            units: "metric", "imperial", or "standard"
            
        Returns:
            Forecast data dict or error dict
        """
        if not self.api_key:
            return {"error": "OpenWeatherMap API key not configured"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/forecast",
                    params={
                        "q": city,
                        "appid": self.api_key,
                        "units": units,
                        "cnt": 8,  # Next 24 hours (3-hour intervals)
                    },
                    timeout=10.0,
                )
                
                if response.status_code == 404:
                    return {"error": f"City '{city}' not found"}
                
                response.raise_for_status()
                data = response.json()
                
                forecasts = []
                for item in data["list"][:5]:
                    forecasts.append({
                        "time": item["dt_txt"],
                        "temperature": item["main"]["temp"],
                        "description": item["weather"][0]["description"],
                    })
                
                return {
                    "city": data["city"]["name"],
                    "country": data["city"]["country"],
                    "forecasts": forecasts,
                    "units": units,
                }
                
        except httpx.HTTPError as e:
            logger.error(f"Weather API error: {e}")
            return {"error": f"Failed to get forecast: {str(e)}"}
    
    async def search(self, query: str) -> str:
        """
        Search for weather information based on a natural language query.
        Extracts city name and returns formatted weather info.
        
        Args:
            query: Natural language query like "weather in London" or "temperature in NYC"
            
        Returns:
            Formatted weather string for LLM context
        """
        # Extract city from query (simple extraction)
        city = self._extract_city(query)
        
        if not city:
            return "Could not determine the city. Please specify a city name."
        
        logger.info(f"🌤️ Getting weather for: {city}")
        
        weather = await self.get_current_weather(city)
        
        if "error" in weather:
            return weather["error"]
        
        # Format for voice response
        unit_symbol = "°C" if weather["units"] == "metric" else "°F"
        wind_unit = "m/s" if weather["units"] == "metric" else "mph"
        
        result = (
            f"Current weather in {weather['city']}, {weather['country']}:\n"
            f"- Temperature: {weather['temperature']}{unit_symbol} (feels like {weather['feels_like']}{unit_symbol})\n"
            f"- Conditions: {weather['description']}\n"
            f"- Humidity: {weather['humidity']}%\n"
            f"- Wind: {weather['wind_speed']} {wind_unit}"
        )
        
        logger.info(f"✅ Weather retrieved for {weather['city']}")
        return result
    
    def _extract_city(self, query: str) -> Optional[str]:
        """Extract city name from a natural language query."""
        query_lower = query.lower()
        
        # Common patterns
        patterns = [
            "weather in ",
            "weather for ",
            "temperature in ",
            "temperature at ",
            "forecast for ",
            "forecast in ",
            "how's the weather in ",
            "what's the weather in ",
            "what is the weather in ",
            "weather of ",
        ]
        
        for pattern in patterns:
            if pattern in query_lower:
                idx = query_lower.find(pattern) + len(pattern)
                city = query[idx:].strip()
                # Clean up common suffixes
                for suffix in ["?", ".", "!", " today", " now", " like", " right now"]:
                    city = city.replace(suffix, "")
                return city.strip()
        
        # If no pattern found, try to extract after common words
        words = query.split()
        for i, word in enumerate(words):
            if word.lower() in ["in", "at", "for"] and i + 1 < len(words):
                return " ".join(words[i + 1:]).strip("?.,!")
        
        # Last resort: if it's a short query, assume it's just the city
        if len(words) <= 3 and "weather" not in query_lower:
            return query.strip("?.,!")
        
        return None


# Singleton instance
weather_tool = WeatherTool()

