import paho.mqtt.client as mqtt
import json
import time
import random
BROKER = "broker.hivemq.com" # Broker público para pruebas
PORT = 1883
TOPIC = "fisi/smat/estaciones/1/lecturas"
client = mqtt.Client()
client.connect(BROKER, PORT)
while True:
    payload = {
        "valor": round(random.uniform(20.0, 60.0), 2),
        "timestamp": time.time()
    }
# Publicar datos en el "Topic"
    client.publish(TOPIC, json.dumps(payload))
    print(f"Enviado por MQTT: {payload}")
    time.sleep(10)
