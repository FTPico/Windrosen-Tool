import requests
import pandas as pd
import matplotlib.pyplot as plt
from windrose import WindroseAxes
from dotenv import load_dotenv
import os
from pathlib import Path
from datetime import datetime, timedelta

# --------------------------
# Einstellungen
# --------------------------
load_dotenv()  # .env Datei einlesen, um Umgebungsvariablen zu laden (API-KEY geheim halten)
API_KEY = os.getenv("OWM_API_KEY")

#Eingabe der Stadt für die Wetterdaten, alternativ Latitude und Longitude verwenden
CITY = "München"   # oder None, wenn du Koordinaten verwenden willst
LAT = 52.4000
LON = 13.0667

if CITY:
    URL = f"http://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&units=metric"
else:
    URL = f"http://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric"

# Sicherstellen, dass der Cache-Ordner existiert
os.makedirs("data", exist_ok=True)

# Daten-Cache pro Stadt
CACHE_FILE = Path(f"data/weather_cache_{CITY.lower()}.csv")
CACHE_EXPIRY_HOURS = 24  # Cache-Lebensdauer

# Ordner für die Grafiken
OUTPUT_DIR = Path("windrose_plots")
OUTPUT_DIR.mkdir(exist_ok=True)

# --------------------------
# Daten abrufen
# --------------------------
def fetch_weather_data():
    """Holt Wetterdaten (Windrichtung + Windgeschwindigkeit) für eine Stadt, mit Caching"""
    # Prüfen, ob Cache existiert und nicht zu alt ist
    if CACHE_FILE.exists():
        modified_time = datetime.fromtimestamp(CACHE_FILE.stat().st_mtime)
        if datetime.now() - modified_time < timedelta(hours=CACHE_EXPIRY_HOURS):
            print("Daten aus Cache laden")
            return pd.read_csv(CACHE_FILE)

    # Cache veraltet oder existiert nicht → API abrufen
    print("Daten von OpenWeatherMap abrufen...")
    response = requests.get(URL)
    response.raise_for_status()
    data = response.json()

    records = []
    for entry in data["list"]:
        dt = entry["dt_txt"]
        wind_speed = entry["wind"]["speed"]
        wind_deg = entry["wind"]["deg"]
        records.append({"datetime": dt, "speed": wind_speed, "direction": wind_deg})

    df = pd.DataFrame(records)
    df.to_csv(CACHE_FILE, index=False)
    return df

# --------------------------
# Windrose plotten
# --------------------------
def plot_windrose(df, city):
    """Zeichnet eine Windrose aus DataFrame mit Spalten speed & direction"""

    # Zeitraum automatisch bestimmen
    start_date = pd.to_datetime(df["datetime"].min()).strftime("%d.%m.%Y %H:%M")
    end_date = pd.to_datetime(df["datetime"].max()).strftime("%d.%m.%Y %H:%M")

    # Windrose erstellen
    ax = WindroseAxes.from_ax()
    ax.bar(
        df["direction"], 
        df["speed"], 
        normed=True, 
        opening=0.8, 
        edgecolor="white"
    )
    legend = ax.set_legend()
    legend.set_title("Windgeschwindigkeit [m/s]")  # Legende klar machen

    # Titel setzen
    plt.title(f"Windrose für {city}\nZeitraum: {start_date} – {end_date}", fontsize=12)

    # Bild speichern
    df['datetime'] = pd.to_datetime(df['datetime'])
    start_str = df['datetime'].min().strftime('%d.%m.%Y_%H-%M')
    end_str = df['datetime'].max().strftime('%d.%m.%Y_%H-%M')
    filename = OUTPUT_DIR / f"windrose_{city}_{start_str}_bis_{end_str}.png"
    plt.savefig(filename, bbox_inches='tight', dpi=300)
    print(f"Windrose gespeichert unter: {filename}")

    plt.show()


# --------------------------
# Main
# --------------------------
def main():
    df = fetch_weather_data()
    print(df.head())  # ersten Zeilen zur Kontrolle
    plot_windrose(df,CITY if CITY else f"Lat {LAT}, Lon {LON}" )

if __name__ == "__main__":
    main()