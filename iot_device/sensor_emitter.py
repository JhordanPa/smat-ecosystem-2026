import requests
import time
import random

# CONFIGURACIÓN
API_URL = "http://localhost:8000/lecturas/"
ESTACION_ID = 1 # ID de la estación registrada en la DB
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbl9maXNpIiwiZXhwIjoxNzc5OTAyNDEzfQ.goDrZa5nzWtzIcjmCyev7Uuek5cV_cWqiRmfYCBXVVk" # Obtenido del login
def leer_sensor_emulado():
    
# Simulamos una lectura de nivel de río (0 a 100 cm)
    return round(random.uniform(10.5, 85.0), 2)
def enviar_telemetria():
    print(f"--- Iniciando Emisor IoT para Estación {ESTACION_ID} ---")
    while True:
        valor = leer_sensor_emulado()
        payload = {
            "valor": valor,
            "estacion_id": ESTACION_ID
        }
        headers = {
            "Authorization": f"Bearer {TOKEN}"
        }
        try:
            response = requests.post(API_URL, json=payload, headers=headers)
            if response.status_code == 200:
                print(f"[OK] Lectura enviada: {valor} cm")
            else:
                print(f"[ERROR] Código: {response.status_code}")
        except Exception as e:
            print(f"[CRÍTICO] No hay conexión con el servidor: {e}")
        
        if valor > 70.0:
            print("[ALERTA] Umbral de inundación superado.")
            time.sleep(2) # Modo Emergencia: envia cada 2 segundos
        else:
            time.sleep(10)
            
# Esperar 5 segundos para la siguiente lectura
        time.sleep(5)
if __name__ == "__main__":
    enviar_telemetria()