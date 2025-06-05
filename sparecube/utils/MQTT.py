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

from paho.mqtt.client import MQTT_ERR_SUCCESS

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
        uniqueLocker: str = "Lockers/Locker:"
        broadcast: str = "Lockers/#"
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

        self.brokers = [
            (self.broker_url, self.broker_port, "Primary"),
            (self.broker_url_bk, self.broker_port, "Backup")
        ]

        self.client.tls_insecure_set(True)  # Set to False in production with valid CA certs



    def connect(self) -> bool:
        print("[MQTT] Connect: Start")

        for url, port, label in self.brokers:
            if not url or not port:
                continue

            try:
                logger.info(f"Attempting MQTT connection to {label} broker at {url}:{port}")
                print(f"Attempting MQTT connection to {label} broker at {url}:{port}")
                resultConn = self.client.connect(url, port)
                print("[MQTT] resultConn: ", resultConn)

                if resultConn == 0:
                    logger.info(f"MQTT connected successfully to {label} broker.")
                    print(f"MQTT connected successfully to {label} broker.")
                    print("[MQTT] Connect: OK")
                    return True
                else:
                    logger.warning(f"Connection attempt to {label} broker failed with result code {resultConn}")

            except Exception as e:
                logger.warning(f"Failed to connect to {label} broker: {e}")

        print("[MQTT] Connect: ERROR Connecting to both servers")
        return False

    # def connect(self) -> bool:
    #     print ("[MQTT] Connect: Start")
    #
    #     for url, port, label in self.brokers:
    #         try:
    #             logger.info(f"Attempting MQTT connection to {label} broker at {url}:{port}")
    #             resultConn = self.client.connect(url, port)
    #             logger.info(f"MQTT connected successfully to {label} broker.")
    #             if resultConn == 0:
    #                 print("[MQTT] Connect: OK")
    #                 return True
    #         except Exception as e:
    #             logger.warning(f"Failed to connect to {label} broker: {e}")
    #             print("[MQTT] Connect: ERROR")
    #             return False
    #
    #     print("[MQTT] Connect: ERROR")
    #     return False



    def disconnect(self):

        try:
            print("[MQTT] Disconnect: Start")
            self.client.disconnect()
            logger.info("Disconnected from MQTT broker")
            print("[MQTT] Disconnect: Ok")
        except:
            print("[MQTT] Disconnect: ERROR")

    def publish_msg(self, msg: MQTT_MSG, qos=2, retain=False) -> bool:
        if self.publish(msg.topic, msg.payload, qos, retain):
            return True
        else:
            return False




    def publish(self, topic: str, payload, qos=2, retain=False) -> bool:
        try:
            print("[MQTT] Publish: Start")
            # Publish and get the result object
            result = self.client.publish(topic, payload, qos=qos, retain=retain)


            # Optional: wait for publish confirmation (especially for QoS 1/2)
            #result.wait_for_publish(5)

            if result [0] == 0:
                logger.info(f"Published to {topic}: {payload}")
                print("[MQTT] Publish: OK")
                return True
               # self.published = True
            else:
                logger.warning(f"Failed to publish to {topic}: {payload}")
                print("[MQTT] Publish: ERROR")
                return False
                #self.published = False

        except Exception as e:
            logger.error(f"Exception during publish to {topic}: {e}")
            print("[MQTT] Publish: ERROR")
            return False
            #self.published = False

        print("[MQTT] Publish: ERROR")
        return False






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