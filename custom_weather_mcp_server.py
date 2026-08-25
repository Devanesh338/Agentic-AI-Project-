from mcp.server.fastmcp import FastMCP
import requests
import os
import sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")

mcp = FastMCP("weather-mcp")


@mcp.tool()
def get_current_weather(city: str) -> str:
    """Get current weather for a city"""
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        response = requests.get(url, timeout=15)

        response.raise_for_status()

        r = response.json()

        if r.get("cod") != 200:
            return f"⚠️ Weather error for {city}: {r.get('message', 'Unknown error')}"

        desc = r["weather"][0]["description"]
        temp = r["main"]["temp"]
        humidity = r["main"]["humidity"]
        wind = r["wind"]["speed"]
        return f"{city}: {desc}, {temp}°C, Humidity {humidity}%, Wind {wind} m/s"

    except Exception as e:
        return f"⚠️ Weather fetch failed for {city}: {e}"


@mcp.tool()
def get_forecast(city: str) -> str:
    """Get 5-day forecast for a city"""
    try:
        url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
        r = requests.get(url).json()

        if r.get("cod") != "200":
            return f"⚠️ Forecast error for {city}: {r.get('message', 'Unknown error')}"

        entries = r["list"][:5]
        lines = [
            f"{e['dt_txt']}: {e['weather'][0]['description']}, {e['main']['temp']}°C"
            for e in entries
        ]
        return "\n".join(lines)

    except Exception as e:
        return f"⚠️ Forecast fetch failed for {city}: {e}"


if __name__ == "__main__":
    mcp.run(transport="stdio")