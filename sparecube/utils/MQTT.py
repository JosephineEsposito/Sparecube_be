# mqtt_manager.py
# Batoul… Create new classes for MQTT
import ssl
import string
from tkinter import Variable

import paho.mqtt.client as mqtt
import threading
import logging
import json
import os


#######################
##  Global Variable  ##
#######################

logger = logging.getLogger(__name__)  # Console logger for monitoring MQTT Connection

########################


# region | Manage Topics
class Topics:
    # Class for declaration the topics that should be sent from the Locker
    class FromLocker:
        pass
    # Class for declaration the topics that should be received by the Locker
    class ToLocker:
        uniqueLocker: str = "lockers/locker:"
        broadcast: str = "Lockers"
# endregion


# region | Manage Message ( Topic & Payload )
class MQTT_MSG:
    def __init__(self, topic: str, payload: dict):
        self.topic = topic
        self.payload = payload

    def to_dict(self):
        return {
            "topic": self.topic,
            "payload": self.payload
        }

    def __str__(self):
        return f"Topic: {self.topic}, Payload: {self.payload}"

# endregion





# region | MQTTManager Class - Handles the client connection and messaging
class MQTTManager:
    def __init__(self, broker_url,broker_url_bk, broker_port=8883, client_id=None, username=None, password=None):
        self.broker_url = broker_url
        self.broker_url_bk = broker_url_bk
        self.broker_port = broker_port
        self.client_id = client_id
        self.username = username
        self.password = password


        self.client = mqtt.Client(client_id=self.client_id)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        self.connected = False
        self.published = False
        self.subscriptions = {}  # topic -> callback function
        self.thread = None

        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)

        # --- Enable SSL/TLS ---
        self.client.tls_set(
            ca_certs=None,
            certfile=None,
            keyfile=None,
            tls_version=ssl.PROTOCOL_TLSv1_2,
            cert_reqs=ssl.CERT_NONE
        )

    def connect(self):
        self._init_variables()
        self.client.tls_insecure_set(True)  # Set to False in production with valid CA certs

        brokers = [
            (self.broker_url, self.broker_port, "Primary"),
            (self.broker_url_bk, self.broker_port, "Backup")
        ]

        self.connected = False

        for url, port, label in brokers:
            try:
                logger.info(f"Attempting MQTT connection to {label} broker at {url}:{port}")
                self.client.connect(url, port)
                self.connected = True
                logger.info(f"MQTT connected successfully to {label} broker.")
                break
            except Exception as e:
                logger.warning(f"Failed to connect to {label} broker: {e}")

        if self.connected:
            self.thread = threading.Thread(target=self.client.loop_forever, daemon=True)
            self.thread.start()
        else:
            logger.error("Failed to connect to any MQTT broker.")


    def disconnect(self):
        self.client.disconnect()
        self._init_variables()
        logger.info("Disconnected from MQTT broker")

    def publish_msg(self, msg: MQTT_MSG, qos=0, retain=False):
        self.publish(msg.topic, msg.payload, qos, retain)



    def publish(self, topic: str, payload, qos=0, retain=False):
        if not isinstance(payload, str):
            payload = json.dumps(payload)

        try:
            # Publish and get the result object
            result = self.client.publish(topic, payload, qos=qos, retain=retain)

            # Optional: wait for publish confirmation (especially for QoS 1/2)
            result.wait_for_publish()

            if result.is_published():
                logger.info(f"Published to {topic}: {payload}")
                self.published = True
            else:
                logger.warning(f"Failed to publish to {topic}: {payload}")
                self.published = False

        except Exception as e:
            logger.error(f"Exception during publish to {topic}: {e}")
            self.published = False

    def subscribe(self, topic: str, callback, qos=0):
        self.subscriptions[topic] = callback
        self.client.subscribe(topic, qos)
        logger.info(f"Subscribed to topic: {topic}")

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode()

        logger.info(f"Message received on {topic}: {payload}")

        handler = self.subscriptions.get(topic)
        if handler:
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                data = payload
            handler(topic, data)
        else:
            logger.warning(f"No handler registered for topic: {topic}")


    def _on_connect(self,client, userdata, flags, rc):
        if rc == 0:
            logger.info("MQTT connected successfully.")
            self.connected = True
            # FOR FUTURE : SUBSCRIBE TO SOME TOPICS TO RECEIVE MESSAGES FROM THEM
          #  self.client.subscribe("home/sensors/temperature")

        else:
            logger.error(f"MQTT failed to connect. Return code: {rc}")
            self.connected = False
        return self.connected

    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        self.connect()
        logger.warning("Disconnected from MQTT broker")


    def _init_variables(self):
        self.connected = False
        self.published = False
        self.subscriptions = {}  # topic -> callback function
        self.thread = None


# endregion End of MQTTManager Class


# region | MQTT Object
mqtt_obj = MQTTManager(
    broker_url=os.getenv("MQTT_BROKER_URL"),
    broker_url_bk=os.getenv("MQTT_BROKER_URL_BK"),
    broker_port=int(os.getenv("MQTT_BROKER_PORT", 8883)),
    client_id=os.getenv("MQTT_CLIENT_ID"),
    username=os.getenv("MQTT_USERNAME"),
    password=os.getenv("MQTT_PASSWORD"),
)
# endregion