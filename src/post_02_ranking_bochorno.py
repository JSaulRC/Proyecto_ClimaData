import requests
import os
import time
import tweepy
from datetime import datetime

COORDENADAS_CLIMA = {
    "Tumbes": {"lat": -3.57, "lon": -80.46},
    "Piura": {"lat": -5.19, "lon": -80.63},
    "Chiclayo": {"lat": -6.77, "lon": -79.84},
    "Trujillo": {"lat": -8.11, "lon": -79.03},
    "Lima": {"lat": -12.04, "lon": -77.02}
}

def generar_ranking():
    datos_ciudades = []
    fecha_reporte = datetime.now().strftime("%d/%m/%Y")

    for ciudad, coords in COORDENADAS_CLIMA.items():
        url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&daily=apparent_temperature_max,uv_index_max&current=relative_humidity_2m&timezone=America%2FLima"
        try:
            datos = requests.get(url).json()
            datos_ciudades.append({
                "ciudad": ciudad,
                "sensacion": datos['daily']['apparent_temperature_max'][0],
                "uv": datos['daily']['uv_index_max'][0],
                "humedad": datos['current']['relative_humidity_2m']
            })
        except: pass
        time.sleep(1)

    datos_ciudades.sort(key=lambda x: x['sensacion'], reverse=True)
    lineas_ranking = []
    
    for i, dato in enumerate(datos_ciudades, 1):
        if dato['uv'] >= 11: nivel_uv = "🟣Extremo"
        elif dato['uv'] >= 8: nivel_uv = "🔴Muy Alto"
        elif dato['uv'] >= 6: nivel_uv = "🟠Alto"
        else: nivel_uv = "🟡Moderado"

        num_str = f"{i}.".ljust(3)
        ciudad_str = dato['ciudad'].ljust(8)
        temp_str = f"{dato['sensacion']:.1f}°C".rjust(6)
        hum_str = f"{dato['humedad']}%".rjust(3)
        uv_str = f"{dato['uv']:.1f} {nivel_uv}".ljust(13)

        lineas_ranking.append(
            f"{num_str} {ciudad_str}: 🔥 SENS: {temp_str} | 💧 Hum: {hum_str} | ☀️ UV: {uv_str}"
        )

    mensaje = (
        f"🚨 Alerta de Bochorno y Radiación | {fecha_reporte}\n\n"
        f"Ranking de sensación térmica y humedad en la costa:\n\n"
        f"{chr(10).join(lineas_ranking)}\n\n"
        f"⚠️ Evite exposición al sol y manténgase hidratado.\n#ElNiño2026 #ClimaData"
    )
    
    publicar_en_x(mensaje)

def publicar_en_x(mensaje):
    cliente = tweepy.Client(
        consumer_key=os.environ.get('X_API_KEY'),
        consumer_secret=os.environ.get('X_API_SECRET'),
        access_token=os.environ.get('X_ACCESS_TOKEN'),
        access_token_secret=os.environ.get('X_ACCESS_SECRET')
    )
    # Sin try/except silencioso para que GitHub te muestre el error real si Twitter lo rechaza
    respuesta = cliente.create_tweet(text=mensaje)
    print(f"✅ Tuit publicado exitosamente. ID: {respuesta.data['id']}")

if __name__ == "__main__":
    generar_ranking()
