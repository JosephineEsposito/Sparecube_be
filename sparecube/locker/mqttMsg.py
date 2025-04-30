#region | IMPORTS

# for Prenotazione
from utils.data import booking

#for MQTT Connection
from utils.MQTT import mqtt_obj, MQTT_MSG, Topics
import logging

#for Message Formating
from utils.JsonHandler import JsonHandler

#######################
##  Global Variable  ##
#######################

logger = logging.getLogger(__name__)  # Console logger for monitoring MQTT Connection

########################

#endregion

#########################################
########## Messages To Lockers ##########
#########################################
class To_Lockers_MSGs :
    # region | Add new reservation
    def addReservMQTTMsg(self: booking, id_torre, id_box) -> bool:
        data = {
        #'timestamp_start': str(self['timestamp_start']),
        #'id_locker': self['id_locker'],
            'idTower': id_torre,
            'myBox': {
                'id': id_box,
                'letteraVettura': self['waybill'],
                'ticket': self['ticket'],
                'statoPrenotazione': self['id_causaleprenotazione']
            }
        }

        #producer = f"Locker:{self['id_locker']}"
        message = "reserve_box"

        mqtt_data = JsonHandler.create_message(message, data)


        mqtt_msg = MQTT_MSG(
        topic=Topics.ToLocker.uniqueLocker + str(self['id_locker']),
        payload=mqtt_data
        )



        if mqtt_obj.connect():
                if mqtt_obj.publish_msg(mqtt_msg):
                    return True


        logger.warning("MQTT MSG NOT PUBLISHED ????")
        return False



    # endregion

    # region | Cancel reservation
    def cancelReservMQTTMsg(prenot: dict) -> bool:
        data = {
            'idTower': prenot['id_torre'],
            'myBox': {
                'id': prenot['id_box'],
                'letteraVettura': prenot['waybill'],
                'ticket': prenot['ticket'],
                'statoPrenotazione': "CANCELED"
            }
        }

      #  producer = f"Locker:{self.id_locker}"
        message = "cancel_reservation"

        mqtt_data = JsonHandler.create_message(message, data)

        mqtt_msg = MQTT_MSG(
            topic=Topics.ToLocker.uniqueLocker + str(prenot['id_locker']),
            payload=mqtt_data
        )

        if mqtt_obj.connect():
            if mqtt_obj.publish_msg(mqtt_msg):
                return True


        logger.warning("MQTT MSG NOT PUBLISHED")
        return False
     # endregion

