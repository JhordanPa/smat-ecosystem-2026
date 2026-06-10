import paho.mqtt.client as mqtt
import requests
import json
import sys
import time

# CONFIGURACIÓN DEL ENTORNO SMAT
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "fisi/smat/estaciones/+/lecturas" # Tópico que coincide con el publisher de la semana 10
API_URL = "http://localhost:8000/lecturas/"
# Token JWT generado previamente desde Swagger o la App móvil para el usuario administrador
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbl9maXNpIiwiZXhwIjoxNzgxMTExNjg2fQ.CVLGvnQS2roJJBAKHX9_eT4FKpHIJf2T7WWppT87DfE"

cache_estaciones = {}

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("🟢 Conectado exitosamente al Broker MQTT")
        
        # Suscribirse al tópico global de lecturas de estaciones
        client.subscribe(MQTT_TOPIC)
        print(f"📡 Escuchando transmisiones en el tópico: {MQTT_TOPIC}")
    else:
        print(f"🔴 Error de conexión al Broker. Código de retorno: {rc}")
        sys.exit(1)
        
def on_message(client, userdata, msg):
    try:
        # 1. Decodificar el payload binario de MQTT a JSON string
        payload_raw = msg.payload.decode("utf-8")
        data_json = json.loads(payload_raw)
        
        # 2. Extraer el ID dinámico de la estación desde la estructura del tópico
        estacion_id = msg.topic.split('/')[-2]
        nuevo_valor = float(data_json["valor"])
        tiempo_actual = time.time()
        
        debe_enviar = False
        
        # 3. LÓGICA DEL FILTRO DEADBAND
        if estacion_id in cache_estaciones:
            ultimo_valor = cache_estaciones[estacion_id]["valor"]
            ultimo_tiempo = cache_estaciones[estacion_id]["tiempo"]
            
            # Calcular variación porcentual absoluta
            variacion = abs(nuevo_valor - ultimo_valor) / ultimo_valor if ultimo_valor != 0 else 0
            tiempo_transcurrido = tiempo_actual - ultimo_tiempo
            
            # Condición: Varía más del 5% O pasaron más de 60 segundos
            if variacion >= 0.05 or tiempo_transcurrido > 60:
                debe_enviar = True
                razon = f"Variación del {variacion*100:.1f}%" if variacion >= 0.05 else f"{tiempo_transcurrido:.0f}s de silencio"
                print(f"📈 [Filtro Aceptado] Estación {estacion_id}: Transmitiendo por {razon}.")
            else:
                # Si no cumple ninguna, se bloquea la petición redundante
                print(f"🚫 [Filtro Bloqueado] Estación {estacion_id}: Valor redundante ({nuevo_valor} cm). Variación insignificante ({variacion*100:.1f}%).")
        else:
            # Si es la primera vez que la estación reporta, pasa directo
            debe_enviar = True
            print(f"🆕 [Filtro Aceptado] Estación {estacion_id}: Primer reporte detectado.")

        # 4. EJECUCIÓN DE INGESTA (Solo si el filtro dio luz verde)
        if debe_enviar:
            # Actualizamos la memoria caché con el nuevo punto de referencia
            cache_estaciones[estacion_id] = {
                "valor": nuevo_valor,
                "tiempo": tiempo_actual
            }
            
            api_payload = {
                "valor": nuevo_valor,
                "estacion_id": int(estacion_id)
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {JWT_TOKEN}"
            }
            
            response = requests.post(API_URL, json=api_payload, headers=headers)
            if response.status_code in [200, 201]:
                print(f"💾 [DB Sincronizada] Lectura de {api_payload['valor']} cm guardada en SQLite.")
            else:
                print(f"⚠️ [Fallo de Ingesta] API rechazó el dato. Código: {response.status_code}")
                
    except KeyError as e:
        print(f"❌ Error de esquema: Falta la llave {e} en el payload MQTT.")
    except ValueError:
        print("❌ Error de casteo: El valor o el ID de la estación no son numéricos.")
    except Exception as e:
        print(f"❌ Error crítico en el Bridge: {e}")
        
# Inicialización del cliente de red MQTT
# Inicialización del cliente de red MQTT (Solo UNA vez y limpio)
bridge_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
bridge_client.on_connect = on_connect
bridge_client.on_message = on_message

try:
    print("🚀 Inicializando el Bridge de Acoplamiento SMAT...")
    bridge_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    # Mantener el hilo escuchando activamente de forma síncrona
    bridge_client.loop_forever()
except KeyboardInterrupt:
    print("\n🛑 Bridge detenido por el usuario.")
    bridge_client.disconnect()