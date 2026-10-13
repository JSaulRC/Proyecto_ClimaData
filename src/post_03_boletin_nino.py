import requests
import pandas as pd
import os
import tweepy
from datetime import datetime, timedelta

def monitoreo_nino12():
    hoy = datetime.now()
    ayer = hoy - timedelta(days=1)
    hace_15_dias = ayer - timedelta(days=14)

    str_inicio = hace_15_dias.strftime('%Y-%m-%d')
    str_fin = ayer.strftime('%Y-%m-%d')

    puntos_nino12 = [
        {"lat": -2.5, "lon": -88.5}, {"lat": -2.5, "lon": -81.5},
        {"lat": -5.0, "lon": -88.5}, {"lat": -5.0, "lon": -82.0},
        {"lat": -8.5, "lon": -88.5}, {"lat": -8.5, "lon": -81.5},
    ]

    CLIMATOLOGIA_NINO12 = {
        1: 24.3, 2: 25.8, 3: 26.2, 4: 25.0, 5: 23.2, 6: 21.6,
        7: 20.6, 8: 19.8, 9: 20.0, 10: 20.7, 11: 21.5, 12: 22.8
    }

    todos_los_datos = []

    for p in puntos_nino12:
        url = f"https://marine-api.open-meteo.com/v1/marine?latitude={p['lat']}&longitude={p['lon']}&daily=sea_surface_temperature_max&start_date={str_inicio}&end_date={str_fin}&timezone=America%2FLima"
        try:
            datos = requests.get(url, timeout=10).json()
            if 'daily' in datos:
                todos_los_datos.append(pd.DataFrame(datos['daily']))
        except: pass

    if not todos_los_datos:
        return

    df_concat = pd.concat(todos_los_datos)
    df_promedio = df_concat.groupby('time')['sea_surface_temperature_max'].mean().reset_index()

    media_climatologica = CLIMATOLOGIA_NINO12.get(hoy.month, 20.7)
    df_promedio['anomalia'] = df_promedio['sea_surface_temperature_max'] - media_climatologica
    df_promedio['fecha_corta'] = pd.to_datetime(df_promedio['time']).dt.strftime('%d/%m')

    texto_post = f"🌊 Monitor El Niño 1+2 | Últimos 15 días\n\nAnomalías térmicas (TSM) en la región Niño 1+2:\n\n"

    for _, fila in df_promedio.iterrows():
        anom = fila['anomalia']
        fecha = fila['fecha_corta']
        tsm_real = fila['sea_surface_temperature_max']

        if anom >= 1.5: emoji = "🔴"
        elif anom >= 0.5: emoji = "🟡"
        elif anom <= -0.5: emoji = "🔵"
        else: emoji = "🟢"

        signo = "+" if anom > 0 else ""
        texto_post += f"{emoji} {fecha}: {signo}{anom:.2f}°C (TSM: {tsm_real:.1f}°C)\n"

    texto_post += "\nDatos: Open-Meteo Marine (NOAA/ECMWF). #ElNiño2026 #ClimaData"
    publicar_en_x(texto_post)

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
    monitoreo_nino12()
