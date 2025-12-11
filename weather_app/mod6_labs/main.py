"""Weather Application using Flet v0.28.3 with Voice Recognition"""
import flet as ft
import json
from pathlib import Path
from weather_service import WeatherService, WeatherServiceError
from voice_service import VoiceService, VoiceServiceError
from config import Config

class WeatherApp:
    """Main Weather Application class."""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.weather_service = WeatherService()
        self.history_file = Path("search_history.json")
        self.search_history = self.load_history()
        self.current_unit = "metric"
        self.current_weather_data = None
        self.is_listening = False
        self.current_alerts = []
        
        # Initialize voice service
        try:
            self.voice_service = VoiceService()
            self.voice_enabled = True
        except VoiceServiceError as e:
            self.voice_service = None
            self.voice_enabled = False
            print(f"Voice services disabled: {e}")
        
        self.setup_page()
        self.build_ui()
    
    def setup_page(self):
        """Configure page settings."""
        self.page.title = Config.APP_TITLE
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 20
        self.page.window.width = Config.APP_WIDTH
        self.page.window.height = Config.APP_HEIGHT
        self.page.window.resizable = True
        self.page.window.center()
    
    def build_ui(self):
        """Build the user interface."""
        # Title with theme toggle
        self.title = ft.Text(
            "🌤️ Weather App",
            size=32,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLUE_700,
        )
        
        self.theme_button = ft.IconButton(
            icon=ft.Icons.DARK_MODE,
            tooltip="Toggle theme",
            on_click=self.toggle_theme,
        )
        
        title_row = ft.Row(
            [self.title, self.theme_button],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        
        # City input field
        self.city_input = ft.TextField(
            label="Enter city name",
            hint_text="e.g., London, Tokyo, New York",
            border_color=ft.Colors.BLUE_400,
            prefix_icon=ft.Icons.LOCATION_CITY,
            autofocus=True,
            on_submit=self.on_search,
            expand=True,
        )
        
        # Search button
        self.search_button = ft.ElevatedButton(
            "Search",
            icon=ft.Icons.SEARCH,
            on_click=self.on_search,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.BLUE_700,
            ),
        )
        
        # Voice button (microphone)
        self.voice_button = ft.IconButton(
            icon=ft.Icons.MIC,
            tooltip="Voice search (click and speak)",
            on_click=self.on_voice_search,
            icon_color=ft.Colors.BLUE_700,
            disabled=not self.voice_enabled,
        )
        
        # Unit toggle button
        self.unit_button = ft.ElevatedButton(
            "°C / °F",
            icon=ft.Icons.THERMOSTAT,
            on_click=self.toggle_units,
        )
        
        # Voice feedback toggle
        self.voice_feedback_checkbox = ft.Checkbox(
            label="Voice feedback",
            value=True,
            disabled=not self.voice_enabled,
        )
        
        # Alerts toggle
        self.alerts_checkbox = ft.Checkbox(
            label="Show weather alerts",
            value=True,
        )
        
        # Search row with voice button
        search_row = ft.Row(
            [self.city_input, self.voice_button, self.search_button],
            spacing=10,
        )
        
        # Controls row
        controls_row = ft.Row(
            [self.unit_button, self.voice_feedback_checkbox, self.alerts_checkbox],
            spacing=10,
            alignment=ft.MainAxisAlignment.START,
        )
        
        # Weather alerts container
        self.alerts_container = ft.Column(
            spacing=8,
            visible=False,
        )
        
        # Weather display container
        self.weather_container = ft.Container(
            visible=False,
            bgcolor=ft.Colors.BLUE_50,
            border_radius=10,
            padding=20,
        )
        
        # Error message
        self.error_message = ft.Text(
            "",
            color=ft.Colors.RED_700,
            visible=False,
        )
        
        # Voice status message
        self.voice_status = ft.Text(
            "",
            color=ft.Colors.BLUE_700,
            visible=False,
            italic=True,
        )
        
        # Loading indicator
        self.loading = ft.ProgressRing(visible=False)
        
        # Info text
        info_parts = ["ℹ️ Enter a city name and click Search to get weather information"]
        if not self.voice_enabled:
            info_parts.append("\n⚠️ Voice recognition unavailable. Install: pip install SpeechRecognition pyttsx3 pyaudio")
        
        self.info_text = ft.Text(
            "\n".join(info_parts),
            color=ft.Colors.GREY_600,
            size=12,
            text_align=ft.TextAlign.CENTER,
        )
        
        # Add all components to page
        self.page.add(
            ft.Column(
                [
                    title_row,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    search_row,
                    controls_row,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    self.loading,
                    self.voice_status,
                    self.alerts_container,
                    self.error_message,
                    self.weather_container,
                    self.info_text,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            )
        )
    
    def create_alert_banner(self, alert: dict) -> ft.Container:
        """Create a visual alert banner for extreme weather conditions."""
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(
                        alert.get("icon", ft.Icons.WARNING),
                        color=alert.get("color", ft.Colors.ORANGE_700),
                        size=24,
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                alert.get("message", "Alert"),
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=alert.get("color", ft.Colors.ORANGE_700),
                            ),
                            ft.Text(
                                alert.get("description", ""),
                                size=12,
                                color=ft.Colors.GREY_700,
                            ),
                            ft.Text(
                                f"💡 {alert.get('recommendation', 'Take necessary precautions')}",
                                size=12,
                                color=ft.Colors.GREY_800,
                                weight=ft.FontWeight.W_500,
                                italic=True,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            bgcolor=alert.get("bg_color", ft.Colors.ORANGE_50),
            border=ft.border.all(1, alert.get("color", ft.Colors.ORANGE_300)),
            border_radius=8,
            padding=12,
            animate_opacity=300,
        )
    
    def display_alerts(self, alerts: list):
        """Display weather alerts if enabled."""
        if not self.alerts_checkbox.value or not alerts:
            self.alerts_container.visible = False
            self.alerts_container.controls.clear()
            return
        
        self.alerts_container.controls.clear()
        
        # Sort alerts by severity (high first)
        severity_order = {"high": 0, "moderate": 1}
        alerts.sort(key=lambda x: severity_order.get(x.get("severity", "moderate"), 2))
        
        # Add header
        self.alerts_container.controls.append(
            ft.Text(
                "⚠️ Weather Alerts & Recommendations",
                size=16,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.BLUE_700,
            )
        )
        
        # Add each alert
        for alert in alerts:
            self.alerts_container.controls.append(
                self.create_alert_banner(alert)
            )
        
        self.alerts_container.visible = True
    
    def toggle_theme(self, e):
        """Toggle between light and dark theme."""
        if self.page.theme_mode == ft.ThemeMode.LIGHT:
            self.page.theme_mode = ft.ThemeMode.DARK
            self.theme_button.icon = ft.Icons.LIGHT_MODE
        else:
            self.page.theme_mode = ft.ThemeMode.LIGHT
            self.theme_button.icon = ft.Icons.DARK_MODE
        self.page.update()
    
    def toggle_units(self, e):
        """Toggle between Celsius and Fahrenheit."""
        if self.current_weather_data is None:
            self.show_error("Please search for a city first")
            return
        
        if self.current_unit == "metric":
            self.current_unit = "imperial"
        else:
            self.current_unit = "metric"
        
        self.display_weather(self.current_weather_data)
        
        # Update alerts with new unit
        if self.current_weather_data:
            self.current_alerts = WeatherService.analyze_extreme_conditions(
                self.current_weather_data, 
                self.current_unit
            )
            self.display_alerts(self.current_alerts)
    
    def on_search(self, e):
        """Handle search button click or enter key press."""
        self.page.run_task(self.get_weather)
    
    def on_voice_search(self, e):
        """Handle voice search button click."""
        if not self.voice_enabled:
            self.show_error("Voice recognition not available")
            return
        
        if self.is_listening:
            return  # Already listening
        
        self.page.run_task(self.voice_search)
    
    async def voice_search(self):
        """Perform voice search."""
        self.is_listening = True
        
        # Update UI
        self.voice_button.icon = ft.Icons.MIC_NONE
        self.voice_button.icon_color = ft.Colors.RED_700
        self.voice_status.value = "🎤 Listening... Please speak the city name"
        self.voice_status.visible = True
        self.error_message.visible = False
        self.page.update()
        
        try:
            # Listen for city name
            city = await self.voice_service.listen_for_city(timeout=5)
            
            # Update status
            self.voice_status.value = f"🎤 Heard: '{city}'"
            self.city_input.value = city
            self.page.update()
            
            # Perform search
            await self.get_weather()
            
        except VoiceServiceError as e:
            self.show_error(str(e))
            self.voice_status.visible = False
        except Exception as e:
            self.show_error(f"Voice error: {str(e)}")
            self.voice_status.visible = False
        finally:
            # Reset UI
            self.is_listening = False
            self.voice_button.icon = ft.Icons.MIC
            self.voice_button.icon_color = ft.Colors.BLUE_700
            self.page.update()
    
    async def get_weather(self):
        """Fetch and display weather data."""
        city = self.city_input.value.strip()
        
        # Validate input
        if not city:
            self.show_error("Please enter a city name")
            return
        
        # Show loading, hide previous results
        self.loading.visible = True
        self.error_message.visible = False
        self.weather_container.visible = False
        self.alerts_container.visible = False
        self.info_text.visible = False
        self.page.update()
        
        try:
            # Fetch weather data
            weather_data = await self.weather_service.get_weather(city)
            self.current_weather_data = weather_data
            
            # Analyze for extreme conditions
            self.current_alerts = WeatherService.analyze_extreme_conditions(
                weather_data, 
                self.current_unit
            )
            
            # Add to history
            self.add_to_history(city)
            
            # Display weather
            self.display_weather(weather_data)
            
            # Display alerts
            self.display_alerts(self.current_alerts)
            
            # Voice feedback if enabled (include alerts in speech)
            if self.voice_enabled and self.voice_feedback_checkbox.value:
                speech_text = self.voice_service.format_weather_speech(
                    weather_data, 
                    self.current_unit
                )
                
                # Add alert information if there are high severity alerts
                high_alerts = [a for a in self.current_alerts if a.get("severity") == "high"]
                if high_alerts:
                    alert_text = " Warning: " + ". ".join([a.get("message", "") for a in high_alerts])
                    speech_text += alert_text
                
                await self.voice_service.speak(speech_text)
            
        except WeatherServiceError as e:
            self.show_error(str(e))
        except Exception as e:
            self.show_error(f"Unexpected error: {str(e)}")
        finally:
            self.loading.visible = False
            self.voice_status.visible = False
            self.page.update()
    
    def display_weather(self, data: dict):
        """Display weather information with unit conversion."""
        # Extract data
        city_name = data.get("name", "Unknown")
        country = data.get("sys", {}).get("country", "")
        temp = data.get("main", {}).get("temp", 0)
        feels_like = data.get("main", {}).get("feels_like", 0)
        temp_max = data.get("main", {}).get("temp_max", 0)
        temp_min = data.get("main", {}).get("temp_min", 0)
        humidity = data.get("main", {}).get("humidity", 0)
        pressure = data.get("main", {}).get("pressure", 0)
        cloudiness = data.get("clouds", {}).get("all", 0)
        description = data.get("weather", [{}])[0].get("description", "").title()
        icon_code = data.get("weather", [{}])[0].get("icon", "01d")
        wind_speed = data.get("wind", {}).get("speed", 0)
        
        # Convert units if necessary
        if self.current_unit == "imperial":
            temp = (temp * 9/5) + 32
            feels_like = (feels_like * 9/5) + 32
            temp_max = (temp_max * 9/5) + 32
            temp_min = (temp_min * 9/5) + 32
            unit_symbol = "°F"
            wind_unit = "mph"
            wind_speed = wind_speed * 2.237  # m/s to mph
        else:
            unit_symbol = "°C"
            wind_unit = "m/s"
        
        # Determine background color based on weather
        bg_color = self.get_weather_color(description)
        
        # Build weather display
        self.weather_container.bgcolor = bg_color
        self.weather_container.content = ft.Column(
            [
                # Location
                ft.Text(
                    f"📍 {city_name}, {country}",
                    size=22,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                ),
                
                # Weather icon and description
                ft.Row(
                    [
                        ft.Image(
                            src=f"https://openweathermap.org/img/wn/{icon_code}@2x.png",
                            width=100,
                            height=100,
                        ),
                        ft.Text(
                            description,
                            size=18,
                            italic=True,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                
                # Temperature
                ft.Text(
                    f"{temp:.1f}{unit_symbol}",
                    size=56,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_900,
                    text_align=ft.TextAlign.CENTER,
                ),
                
                ft.Text(
                    f"Feels like {feels_like:.1f}{unit_symbol}",
                    size=14,
                    color=ft.Colors.GREY_700,
                    text_align=ft.TextAlign.CENTER,
                ),
                
                # High/Low temps
                ft.Text(
                    f"↑ {temp_max:.1f}{unit_symbol}  ↓ {temp_min:.1f}{unit_symbol}",
                    size=12,
                    color=ft.Colors.GREY_700,
                    text_align=ft.TextAlign.CENTER,
                ),
                
                ft.Divider(),
                
                # Weather metrics in 2x2 grid
                ft.Row(
                    [
                        self.create_info_card(
                            ft.Icons.WATER_DROP,
                            "Humidity",
                            f"{humidity}%",
                        ),
                        self.create_info_card(
                            ft.Icons.AIR,
                            "Wind Speed",
                            f"{wind_speed:.2f} {wind_unit}",
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                    spacing=10,
                ),
                
                ft.Row(
                    [
                        self.create_info_card(
                            ft.Icons.SPEED,
                            "Pressure",
                            f"{pressure} hPa",
                        ),
                        self.create_info_card(
                            ft.Icons.CLOUD,
                            "Cloudiness",
                            f"{cloudiness}%",
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                    spacing=10,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        )
        
        self.weather_container.visible = True
        self.error_message.visible = False
        self.info_text.visible = False
        self.page.update()
    
    def create_info_card(self, icon, label, value):
        """Create an info card for weather details."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(icon, size=28, color=ft.Colors.BLUE_700),
                    ft.Text(label, size=11, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_500),
                    ft.Text(
                        value,
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_900,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
            ),
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            padding=15,
            expand=True,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=3,
                color=ft.Colors.GREY_300,
                offset=ft.Offset(0, 2),
            ),
        )
    
    def get_weather_color(self, description: str) -> str:
        """Get background color based on weather condition."""
        desc_lower = description.lower()
        
        if "rain" in desc_lower or "drizzle" in desc_lower:
            return ft.Colors.INDIGO_50
        elif "cloud" in desc_lower or "overcast" in desc_lower:
            return ft.Colors.GREY_100
        elif "sunny" in desc_lower or "clear" in desc_lower:
            return ft.Colors.AMBER_50
        elif "snow" in desc_lower:
            return ft.Colors.LIGHT_BLUE_50
        elif "storm" in desc_lower or "thunder" in desc_lower:
            return ft.Colors.PURPLE_50
        else:
            return ft.Colors.BLUE_50
    
    def show_error(self, message: str):
        """Display error message."""
        self.error_message.value = f"❌ {message}"
        self.error_message.visible = True
        self.weather_container.visible = False
        self.alerts_container.visible = False
        self.info_text.visible = True
        self.page.update()
    
    # Search History Methods
    def load_history(self):
        """Load search history from file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_history(self):
        """Save search history to file."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.search_history, f)
        except:
            pass
    
    def add_to_history(self, city: str):
        """Add city to search history."""
        if city not in self.search_history:
            self.search_history.insert(0, city)
            self.search_history = self.search_history[:10]  # Keep last 10
            self.save_history()

def main(page: ft.Page):
    """Main entry point."""
    WeatherApp(page)

if __name__ == "__main__":
    ft.app(target=main)