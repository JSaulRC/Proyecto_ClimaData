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

COORDENADAS_MAR = {
    "Tumbes": {"lat": -3.57, "lon": -80.46},
    "Piura": {"lat": -5.08, "lon": -81.11}, 
    "Chiclayo": {"lat": -6.77, "lon": -79.84},
    "Trujillo": {"lat": -8.11, "lon": -79.03},
    "Lima": {"lat": -12.04, "lon": -77.02}
}

PROMEDIO_HISTORICO = {
    "Tumbes": 26.5, "Piura": 25.0, "Chiclayo": 23.5, "Trujillo": 21.0, "Lima": 19.5
}

def generar_boletin_diario():
    nombres_ciudades = list(COORDENADAS_CLIMA.keys())
    fecha_reporte = datetime.now().strftime("%d/%m/%Y")
    
    reporte_lineas = [
        "UBICACIÓN | ATMÓSFERA | OCÉANO(TSM) | HUMEDAD | PRESIÓN",
        "-------------------------------------------------------"
    ]

    for ciudad in nombres_ciudades:
        lat_c, lon_c = COORDENADAS_CLIMA[ciudad]['lat'], COORDENADAS_CLIMA[ciudad]['lon']
        lat_m, lon_m = COORDENADAS_MAR[ciudad]['lat'], COORDENADAS_MAR[ciudad]['lon']

        url_clima = f"https://api.open-meteo.com/v1/forecast?latitude={lat_c}&longitude={lon_c}&daily=temperature_2m_max&current=relative_humidity_2m,surface_pressure&timezone=America%2FLima"
        url_mar = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat_m}&longitude={lon_m}&hourly=sea_surface_temperature&timezone=America%2FLima"
        
        temp_max, presion, humedad, sst_actual = "N/A", "N/A", "N/A", "N/A"
        alerta = "🟢"
        
        try:
            datos_c = requests.get(url_clima).json()
            temp_max = datos_c['daily']['temperature_2m_max'][0]
            humedad = datos_c['current']['relative_humidity_2m']
            presion = datos_c['current']['surface_pressure']
            
            diferencia = temp_max - PROMEDIO_HISTORICO[ciudad]
            if diferencia >= 2.0: alerta = "🔴"
            elif diferencia >= 0.5: alerta = "🟡"
        except: pass

        try:
            sst_actual = requests.get(url_mar).json()['hourly']['sea_surface_temperature'][0]
        except: pass
        
        ciudad_format = ciudad.ljust(8)
        t_fmt = f"{temp_max:.1f}°C" if temp_max != "N/A" else "N/A"
        tsm_fmt = f"{sst_actual:.1f}°C" if sst_actual != "N/A" else "N/A"
        p_fmt = f"{presion:.1f}hPa" if presion != "N/A" else "N/A"
        h_fmt = f"{humedad:.0f}%" if humedad != "N/A" else "N/A"
        
        reporte_lineas.append(
            f"{alerta} {ciudad_format}: 🌡️{t_fmt.rjust(6)} | 🌊TSM:{tsm_fmt.rjust(6)} | 💧{h_fmt.rjust(4)} | 🌪️ {p_fmt}"
        )
        time.sleep(1)

    cuerpo_texto = "\n".join(reporte_lineas)
    tuit_final = (
        f"📡 Reporte Costa Peruana | {fecha_reporte}\n\n"
        f"{cuerpo_texto}\n\n"
        f"Monitoreo de anomalías #ElNiño2026 #ClimaData"
    )
    
    publicar_en_x(tuit_final)

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
    generar_boletin_diario()
