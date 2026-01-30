"""
Weather Service
Fetches weather data and assesses impact on logistics using WeatherAPI.com
"""
import requests
from config import Config

class WeatherService:
    def __init__(self):
        self.api_key = Config.WEATHERAPI_KEY
        
    def get_weather_impact(self, country, city=None):
        """
        Get weather data and assess impact on importing operations
        
        Args:
            country: Country name
            city: Optional city name (uses capital if not provided)
            
        Returns:
            Dictionary with weather data and impact assessment
        """
        try:
            # Get weather data
            weather_data = self._fetch_weather(country, city)
            
            if not weather_data:
                return {
                    'status': 'unavailable',
                    'message': 'Weather data unavailable'
                }
            
            # Assess impact
            impact = self._assess_weather_impact(weather_data)
            
            return {
                'status': 'success',
                'weather': weather_data,
                'impact': impact
            }
            
        except Exception as e:
            print(f"Error getting weather impact: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _fetch_weather(self, country, city=None):
        """Fetch current weather data from WeatherAPI.com"""
        try:
            # Use city if provided, otherwise use country
            location = city if city else country
            
            params = {
                'key': self.api_key,
                'q': location,
                'aqi': 'no'
            }
            
            response = requests.get(Config.WEATHERAPI_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            location_data = data.get('location', {})
            current = data.get('current', {})
            condition = current.get('condition', {})
            
            return {
                'location': location_data.get('name', location),
                'country': location_data.get('country', ''),
                'region': location_data.get('region', ''),
                'temperature': current.get('temp_c', 0),
                'feels_like': current.get('feelslike_c', 0),
                'humidity': current.get('humidity', 0),
                'pressure': current.get('pressure_mb', 0),
                'weather': condition.get('text', 'Unknown'),
                'weather_code': condition.get('code', 0),
                'wind_speed': current.get('wind_kph', 0) / 3.6,  # Convert to m/s
                'wind_direction': current.get('wind_dir', ''),
                'wind_gust': current.get('gust_kph', 0) / 3.6,  # Convert to m/s
                'clouds': current.get('cloud', 0),
                'visibility': current.get('vis_km', 10),
                'precipitation': current.get('precip_mm', 0),
                'uv_index': current.get('uv', 0),
                'last_updated': current.get('last_updated', '')
            }
            
        except Exception as e:
            print(f"Error fetching weather: {e}")
            return None
    
    def _assess_weather_impact(self, weather_data):
        """Assess the impact of weather on logistics and shipping"""
        severity = 0
        factors = []
        recommendations = []
        
        # Check wind speed (high winds affect shipping)
        wind_speed = weather_data.get('wind_speed', 0)
        wind_gust = weather_data.get('wind_gust', 0)
        
        if wind_gust > 25 or wind_speed > 20:  # Very strong winds
            severity += 4
            factors.append(f"Very strong winds (Speed: {wind_speed:.1f} m/s, Gusts: {wind_gust:.1f} m/s)")
            recommendations.append("Expect significant shipping delays and possible port closures")
        elif wind_gust > 15 or wind_speed > 10:
            severity += 2
            factors.append(f"Strong winds (Speed: {wind_speed:.1f} m/s, Gusts: {wind_gust:.1f} m/s)")
            recommendations.append("Monitor shipping schedules for potential delays")
        
        # Check weather conditions
        weather_main = weather_data.get('weather', '').lower()
        weather_code = weather_data.get('weather_code', 0)
        
        # Severe weather codes (based on WeatherAPI codes)
        if weather_code in [1087, 1273, 1276, 1279, 1282]:  # Thunderstorms
            severity += 3
            factors.append(f"Thunderstorm conditions: {weather_data.get('weather', '')}")
            recommendations.append("Expect significant shipping and logistics delays")
        elif weather_code in [1066, 1069, 1072, 1114, 1117, 1210, 1213, 1216, 1219, 1222, 1225, 1237, 1255, 1258, 1261, 1264]:  # Snow/Ice
            severity += 2
            factors.append(f"Snow/Ice conditions: {weather_data.get('weather', '')}")
            recommendations.append("Possible road and port delays due to snow/ice")
        elif 'rain' in weather_main or 'drizzle' in weather_main:
            severity += 1
            factors.append(f"Rainy conditions: {weather_data.get('weather', '')}")
        
        # Check precipitation
        precipitation = weather_data.get('precipitation', 0)
        if precipitation > 50:  # Heavy rain
            severity += 2
            factors.append(f"Heavy precipitation ({precipitation} mm)")
            recommendations.append("Heavy rain may affect ground transportation")
        
        # Check visibility
        visibility = weather_data.get('visibility', 10)
        if visibility < 1:  # Less than 1 km
            severity += 3
            factors.append(f"Very poor visibility ({visibility} km)")
            recommendations.append("Severe visibility issues may halt port operations")
        elif visibility < 5:
            severity += 1
            factors.append(f"Reduced visibility ({visibility} km)")
        
        # Check extreme temperatures (affects some products)
        temp = weather_data.get('temperature', 20)
        if temp > 40:
            severity += 2
            factors.append(f"Extreme heat ({temp}°C)")
            recommendations.append("Monitor temperature-sensitive cargo closely")
        elif temp < -10:
            severity += 2
            factors.append(f"Extreme cold ({temp}°C)")
            recommendations.append("Cold weather may affect cargo and equipment")
        
        # Determine impact level
        if severity == 0:
            impact_level = "minimal"
            summary = "Weather conditions are favorable for logistics operations"
        elif severity <= 3:
            impact_level = "low"
            summary = "Minor weather-related delays possible"
        elif severity <= 6:
            impact_level = "moderate"
            summary = "Weather may cause noticeable delays in shipping and logistics"
        else:
            impact_level = "high"
            summary = "Severe weather likely to disrupt logistics operations significantly"
        
        return {
            'severity_score': min(severity, 10),
            'impact_level': impact_level,
            'summary': summary,
            'factors': factors,
            'recommendations': recommendations if recommendations else ["Monitor weather updates regularly"]
        }
