import requests
import pandas as pd
import os
import tweepy
from datetime import datetime

# Diccionario de ciudades costeras estratégicas (De Norte a Sur)
CIUDADES_COSTA = {
    "Tumbes": {"lat": -3.57, "lon": -80.46},
    "Piura": {"lat": -5.19, "lon": -80.63},
    "Chiclayo": {"lat": -6.77, "lon": -79.84},
    "Trujillo": {"lat": -8.11, "lon": -79.03},
    "Lima": {"lat": -12.04, "lon": -77.02}
}

def obtener_datos_costa():
    reporte_ciudades = []
    fecha_reporte = ""

    for ciudad, coords in CIUDADES_COSTA.items():
        # 1. Consulta atmosférica
        url_clima = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={coords['lat']}&longitude={coords['lon']}"
            f"&daily=temperature_2m_max,precipitation_sum"
            f"&timezone=America%2FLima"
        )
        
        # 2. Consulta oceánica (TSM de la NOAA)
        url_mar = (
            f"https://marine-api.open-meteo.com/v1/marine?"
            f"latitude={coords['lat']}&longitude={coords['lon']}"
            f"&hourly=ocean_temperature&timezone=America%2FLima"
        )
        
        try:
            # Extraer Clima
            resp_clima = requests.get(url_clima)
            resp_clima.raise_for_status()
            datos_clima = resp_clima.json()['daily']
            
            if not fecha_reporte:
                # Transformar fecha de YYYY-MM-DD a DD/MM/AAAA
                fecha_raw = datos_clima['time'][0]
                fecha_obj = datetime.strptime(fecha_raw, "%Y-%m-%d")
                fecha_reporte = fecha_obj.strftime("%d/%m/%Y")
                
            temp_max = datos_clima['temperature_2m_max'][0]
            precipitacion = datos_clima['precipitation_sum'][0]
            
            # Extraer Mar
            resp_mar = requests.get(url_mar)
            resp_mar.raise_for_status()
            datos_mar = resp_mar.json()
            sst_actual = datos_mar['hourly']['ocean_temperature'][0]

            # Semáforo de riesgo por lluvia
            if precipitacion >= 5.0:
                alerta = "🔴"
            elif precipitacion > 0.0:
                alerta = "🟡"
            else:
                alerta = "🟢"
                
            # Formatear y alinear en columnas usando espacios
            # .ljust(8) alinea a la izquierda rellenando hasta 8 caracteres (Chiclayo)
            # .rjust(6) alinea los números a la derecha para que los decimales cuadren
            ciudad_format = ciudad.ljust(8)
            temp_format = f"{temp_max:.1f}°C".rjust(6)
            prec_format = f"{precipitacion:.1f}mm".rjust(6)
            tsm_format = f"{sst_actual:.1f}°C".rjust(6)
            
            # Formato compacto por ciudad (TSM reemplaza a SST)
            reporte_ciudades.append(
                f"{alerta} {ciudad_format}: 🌡️{temp_format} | 🌧️{prec_format} | 🌊TSM: {tsm_format}"
            )

        except Exception as e:
            print(f"Error procesando {ciudad}: {e}")
            reporte_ciudades.append(f"⚪ {ciudad.ljust(8)}: Datos no disponibles")

    # Ensamblar el mensaje final para X
    cuerpo = "\n".join(reporte_ciudades)
    mensaje = (
        f"📡 Reporte Costa Peruana | {fecha_reporte}\n\n"
        f"{cuerpo}\n\n"
        f"Monitoreo de anomalías #ElNiño2026 #ClimaData"
    )

    print("Extracción exitosa. Mensaje generado:")
    print("-" * 40)
    print(mensaje)
    print("-" * 40)

    # Intentar publicar
    publicar_en_x(mensaje)

def publicar_en_x(mensaje):
    api_key = os.environ.get('X_API_KEY')
    api_secret = os.environ.get('X_API_SECRET')
    access_token = os.environ.get('X_ACCESS_TOKEN')
    access_secret = os.environ.get('X_ACCESS_SECRET')

    try:
        cliente = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret
        )
        respuesta = cliente.create_tweet(text=mensaje)
        print(f"¡Éxito! Tuit publicado correctamente. ID: {respuesta.data['id']}")
    except Exception as e:
        print(f"Error al publicar en X: {e}")

if __name__ == "__main__":
    obtener_datos_costa()
