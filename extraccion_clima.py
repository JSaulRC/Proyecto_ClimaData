import requests
import pandas as pd
import os
import tweepy

# Coordenadas estratégicas del litoral peruano
CIUDADES_COSTA = {
    "Tumbes": {"lat": -3.57, "lon": -80.46},
    "Piura": {"lat": -5.19, "lon": -80.63},
    "Chiclayo": {"lat": -6.77, "lon": -79.84},
    "Trujillo": {"lat": -8.11, "lon": -79.03},
    "Lima": {"lat": -12.04, "lon": -77.02}
}

def procesar_clima_diario():
    # 1. Cargar la base de datos histórica
    ruta_csv = "historico_climadata.csv"
    
    try:
        df_historico = pd.read_csv(ruta_csv)
    except FileNotFoundError:
        print("Error: No se encontró la base de datos histórica.")
        return

    alertas_generadas = []
    reporte_resumen = []
    fecha_hoy = ""

    for ciudad, coords in CIUDADES_COSTA.items():
        # Calcular estadísticas de la década para esta ciudad específica
        hist_ciudad = df_historico[df_historico['ciudad'] == ciudad]
        promedio_temp = hist_ciudad['temp_max'].mean()
        max_hist_temp = hist_ciudad['temp_max'].max()

        # Consultar el clima de HOY en Open-Meteo
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={coords['lat']}&longitude={coords['lon']}"
            f"&daily=temperature_2m_max,precipitation_sum"
            f"&timezone=America%2FLima"
        )
        
        try:
            respuesta = requests.get(url)
            respuesta.raise_for_status()
            datos = respuesta.json()['daily']
            
            if not fecha_hoy:
                fecha_hoy = datos['time'][0]
                
            temp_max_hoy = datos['temperature_2m_max'][0]
            precipitacion_hoy = datos['precipitation_sum'][0]
            
            # --- MOTOR DE ANOMALÍAS Y RÉCORDS ---
            # Si rompe el récord de 10 años
            if temp_max_hoy >= max_hist_temp:
                alertas_generadas.append(
                    f"🚨 #RécordClimaData | {ciudad}\n"
                    f"Hoy se proyectan {temp_max_hoy}°C. ¡Es el valor más alto registrado en nuestra base de datos de la última década! 📈🔥\n"
                    f"(Récord anterior: {max_hist_temp}°C)"
                )
            # Si supera el promedio de forma inusual (ej. +2.5°C por encima de la media de 10 años)
            elif temp_max_hoy > (promedio_temp + 2.5):
                alertas_generadas.append(
                    f"⚠️ Alerta Térmica | {ciudad}\n"
                    f"Temperatura de hoy ({temp_max_hoy}°C) supera severamente su promedio histórico de 10 años ({promedio_temp:.1f}°C). Tomen precauciones. ☀️"
                )

            # Lógica visual del resumen
            if precipitacion_hoy >= 5.0:
                alerta = "🔴"
            elif precipitacion_hoy > 0.0:
                alerta = "🟡"
            else:
                alerta = "🟢"
                
            reporte_resumen.append(f"{alerta} {ciudad}: {temp_max_hoy}°C (Media hist: {promedio_temp:.1f}°C)")

        except Exception as e:
            print(f"Error procesando {ciudad}: {e}")

    # --- ENSAMBLAR Y PUBLICAR EN X ---
    # Publicamos primero las alertas de urgencia si las hay
    for alerta_msj in alertas_generadas:
        print(f"\nGenerando Alerta:\n{alerta_msj}")
        publicar_en_x(alerta_msj)

    # Luego publicamos el resumen diario comparativo
    cuerpo = "\n".join(reporte_resumen)
    mensaje_diario = (
        f"📊 Reporte Comparativo | {fecha_hoy}\n\n"
        f"{cuerpo}\n\n"
        f"Datos de hoy cruzados con el histórico de 10 años. #ElNiño2026 #ClimaData"
    )
    
    print(f"\nGenerando Resumen:\n{mensaje_diario}")
    publicar_en_x(mensaje_diario)

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
        # Si estás probando en entorno sin credenciales, comenta la línea de abajo temporalmente:
        respuesta = cliente.create_tweet(text=mensaje)
        print(f"¡Tuit publicado en @ClimaData! ID: {respuesta.data['id']}")
    except Exception as e:
        print(f"Error al publicar en X: {e}")

if __name__ == "__main__":
    procesar_clima_diario()
