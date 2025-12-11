"""Weather service for fetching weather data from OpenWeatherMap API."""
import httpx
from config import Config


class WeatherServiceError(Exception):
    """Custom exception for weather service errors."""
    pass


class WeatherService:
    """Service for fetching weather data."""

    def __init__(self):
        self.api_key = Config.API_KEY
        self.base_url = Config.BASE_URL
        self.units = Config.UNITS
        self.timeout = Config.TIMEOUT

    async def get_weather(self, city: str) -> dict:
        """Fetch weather data for a given city.

        Args:
            city: The city name to fetch weather for.

        Returns:
            Dictionary containing weather data.

        Raises:
            WeatherServiceError: If city is invalid or API call fails.
        """
        if not city.strip():
            raise WeatherServiceError("City name cannot be empty")

        params = {
            "q": city.strip(),
            "appid": self.api_key,
            "units": self.units
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()
                return data
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise WeatherServiceError(f"City '{city}' not found")
                else:
                    raise WeatherServiceError(f"API error: {e.response.status_code}")
            except httpx.RequestError as e:
                raise WeatherServiceError(f"Request failed: {str(e)}")
            except Exception as e:
                raise WeatherServiceError(f"Unexpected error: {str(e)}")

    @staticmethod
    def analyze_extreme_conditions(data: dict, unit: str = "metric") -> list:
        """Analyze weather data for extreme conditions and generate alerts.
        
        Args:
            data: Weather data dictionary
            unit: Temperature unit ('metric' or 'imperial')
            
        Returns:
            List of alert dictionaries with type, message, severity, and recommendation
        """
        alerts = []
        temp = data.get("main", {}).get("temp", 0)
        feels_like = data.get("main", {}).get("feels_like", 0)
        humidity = data.get("main", {}).get("humidity", 0)
        wind_speed = data.get("wind", {}).get("speed", 0)
        weather_id = data.get("weather", [{}])[0].get("id", 800)
        
        # Convert to Celsius for consistent threshold checking
        if unit == "imperial":
            temp_c = (temp - 32) * 5/9
            feels_like_c = (feels_like - 32) * 5/9
        else:
            temp_c = temp
            feels_like_c = feels_like
        
        # Temperature alerts
        if temp_c >= 35:  # Very hot
            alerts.append({
                "type": "temperature",
                "severity": "high",
                "message": "🌡️ Extreme Heat Warning",
                "description": f"Temperature is {temp:.1f}°{'F' if unit == 'imperial' else 'C'}",
                "recommendation": "Stay hydrated, avoid direct sun, and wear lightweight clothing",
                "icon": "WARNING_AMBER",
                "color": "RED_700",
                "bg_color": "RED_50"
            })
        elif temp_c >= 30:
            alerts.append({
                "type": "temperature",
                "severity": "moderate",
                "message": "☀️ High Temperature",
                "description": f"Temperature is {temp:.1f}°{'F' if unit == 'imperial' else 'C'}",
                "recommendation": "Wear sunscreen and stay hydrated",
                "icon": "WB_SUNNY",
                "color": "ORANGE_700",
                "bg_color": "ORANGE_50"
            })
        elif temp_c <= -10:  # Very cold
            alerts.append({
                "type": "temperature",
                "severity": "high",
                "message": "🥶 Extreme Cold Warning",
                "description": f"Temperature is {temp:.1f}°{'F' if unit == 'imperial' else 'C'}",
                "recommendation": "Wear multiple layers, cover exposed skin, and limit outdoor time",
                "icon": "AC_UNIT",
                "color": "BLUE_700",
                "bg_color": "BLUE_50"
            })
        elif temp_c <= 0:
            alerts.append({
                "type": "temperature",
                "severity": "moderate",
                "message": "❄️ Freezing Temperature",
                "description": f"Temperature is {temp:.1f}°{'F' if unit == 'imperial' else 'C'}",
                "recommendation": "Wear warm clothing and watch for ice on roads",
                "icon": "AC_UNIT",
                "color": "CYAN_700",
                "bg_color": "CYAN_50"
            })
        
        # Feels-like temperature alerts (wind chill/heat index)
        if feels_like_c >= 40:
            alerts.append({
                "type": "feels_like",
                "severity": "high",
                "message": "🔥 Dangerous Heat Index",
                "description": f"Feels like {feels_like:.1f}°{'F' if unit == 'imperial' else 'C'}",
                "recommendation": "Avoid strenuous activity, seek air conditioning, drink plenty of water",
                "icon": "LOCAL_FIRE_DEPARTMENT",
                "color": "DEEP_ORANGE_700",
                "bg_color": "DEEP_ORANGE_50"
            })
        elif feels_like_c <= -20:
            alerts.append({
                "type": "feels_like",
                "severity": "high",
                "message": "💨 Extreme Wind Chill",
                "description": f"Feels like {feels_like:.1f}°{'F' if unit == 'imperial' else 'C'}",
                "recommendation": "Limit time outdoors, cover all exposed skin, frostbite risk is high",
                "icon": "AIR",
                "color": "INDIGO_700",
                "bg_color": "INDIGO_50"
            })
        
        # Humidity alerts
        if humidity >= 90:
            alerts.append({
                "type": "humidity",
                "severity": "moderate",
                "message": "💦 Very High Humidity",
                "description": f"Humidity is {humidity}%",
                "recommendation": "Stay hydrated and avoid strenuous activity",
                "icon": "WATER_DROP",
                "color": "TEAL_700",
                "bg_color": "TEAL_50"
            })
        elif humidity <= 20:
            alerts.append({
                "type": "humidity",
                "severity": "moderate",
                "message": "🏜️ Low Humidity",
                "description": f"Humidity is {humidity}%",
                "recommendation": "Use moisturizer and stay hydrated",
                "icon": "WATER_DROP",
                "color": "AMBER_700",
                "bg_color": "AMBER_50"
            })
        
        # Wind speed alerts (m/s)
        wind_mps = wind_speed if unit == "metric" else wind_speed / 2.237
        if wind_mps >= 20:  # Strong gale
            alerts.append({
                "type": "wind",
                "severity": "high",
                "message": "💨 High Wind Warning",
                "description": f"Wind speed is {wind_speed:.1f} {'mph' if unit == 'imperial' else 'm/s'}",
                "recommendation": "Secure loose objects, avoid outdoor activities",
                "icon": "AIR",
                "color": "PURPLE_700",
                "bg_color": "PURPLE_50"
            })
        elif wind_mps >= 10:
            alerts.append({
                "type": "wind",
                "severity": "moderate",
                "message": "🌬️ Windy Conditions",
                "description": f"Wind speed is {wind_speed:.1f} {'mph' if unit == 'imperial' else 'm/s'}",
                "recommendation": "Hold onto hats and lightweight items",
                "icon": "AIR",
                "color": "BLUE_GREY_700",
                "bg_color": "BLUE_GREY_50"
            })
        
        # Weather condition alerts based on OpenWeatherMap IDs
        # Thunderstorm
        if 200 <= weather_id < 300:
            alerts.append({
                "type": "storm",
                "severity": "high",
                "message": "⛈️ Thunderstorm Alert",
                "description": "Thunderstorm in the area",
                "recommendation": "Seek indoor shelter, avoid open areas and tall objects",
                "icon": "FLASH_ON",
                "color": "DEEP_PURPLE_700",
                "bg_color": "DEEP_PURPLE_50"
            })
        
        # Heavy rain
        elif 500 <= weather_id < 600 and weather_id not in [500, 501]:  # Exclude light rain
            alerts.append({
                "type": "rain",
                "severity": "moderate",
                "message": "🌧️ Heavy Rain",
                "description": "Heavy rainfall expected",
                "recommendation": "Bring an umbrella, use caution when driving",
                "icon": "BEACH_ACCESS",
                "color": "BLUE_700",
                "bg_color": "BLUE_50"
            })
        
        # Snow
        elif 600 <= weather_id < 700:
            alerts.append({
                "type": "snow",
                "severity": "moderate" if weather_id < 602 else "high",
                "message": "❄️ Snow Alert",
                "description": "Snowfall expected",
                "recommendation": "Allow extra travel time, drive cautiously",
                "icon": "AC_UNIT",
                "color": "LIGHT_BLUE_700",
                "bg_color": "LIGHT_BLUE_50"
            })
        
        # Fog/mist
        elif 700 <= weather_id < 800:
            alerts.append({
                "type": "fog",
                "severity": "moderate",
                "message": "🌫️ Reduced Visibility",
                "description": "Fog or mist reducing visibility",
                "recommendation": "Use low beam headlights, drive slowly",
                "icon": "FOGGY",
                "color": "GREY_700",
                "bg_color": "GREY_50"
            })
        
        return alerts