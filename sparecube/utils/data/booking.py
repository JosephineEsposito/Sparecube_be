"""
Manager of Booking data
"""

from .. import crypt as c


class Booking():
    def __init__(self, args = None):
        if args is None:
            # default values for attributes if args is not provided
            self.timestamp_start            = None
            self.timestamp_end              = None
            self.waybill                    = None
            self.ticket                     = None
            self.id_utente                  = None
            self.id_locker                  = None
            self.id_cassetto                = None
            self.id_causaleprenotazione     = None
        else:
            # initialize attributes with values from args dictionary (from database)
            self.timestamp_start            = args.get('timestamp_start')
            self.timestamp_end              = args.get('timestamp_end')
            self.waybill                    = args.get('waybill')
            self.ticket                     = args.get('ticket')
            self.id_utente                  = args.get('id_utente')
            self.id_locker                  = args.get('id_locker')
            self.id_cassetto                = args.get('id_cassetto')
            self.id_causaleprenotazione     = args.get('id_causaleprenotazione')
    
    def json(self):
        data = {}

        if self.timestamp_start         : data['timestamp_start']               = self.timestamp_start
        if self.timestamp_end           : data['timestamp_end']                 = self.timestamp_end
        if self.waybill                 : data['waybill']                       = self.waybill
        if self.ticket                  : data['ticket']                        = self.ticket
        if self.id_utente               : data['id_utente']                     = self.id_utente
        if self.id_locker               : data['id_locker']                     = self.id_locker
        if self.id_cassetto             : data['id_cassetto']                   = self.id_cassetto
        if self.id_causaleprenotazione  : data['id_causaleprenotazione']        = self.id_causaleprenotazione

        return data
    
    def clean(self):
        self.timestamp_start            = None
        self.timestamp_end              = None
        self.waybill                    = None
        self.ticket                     = None
        self.id_utente                  = None
        self.id_locker                  = None
        self.id_cassetto                = None
        self.id_causaleprenotazione     = None

    def base(self):
        return {
            "timestamp_start" : "0000-00-00",
            "timestamp_end" : "0000-00-00",
            "waybill" : "",
            "ticket" : "",
            "id_utente" : 0,
            "id_locker" : 0,
            "id_cassetto" : 0,
            "id_causaleprenotazione" : 0,
        }
    
    def query(self, o):
        data = []
        if "timestamp_end" in o:
            data.append(f"timestamp_end = {o["timestamp_end"]}")
        if "waybill" in o:
            data.append(f"waybill = {o["waybill"]}")
        if "ticket" in o:
            data.append(f"ticket = {o["ticket"]}")
        if "id_utente" in o:
            data.append(f"id_utente = {o["id_utente"]}")
        if "id_locker" in o:
            data.append(f"id_locker = {o["id_locker"]}")
        if "id_cassetto" in o:
            data.append(f"id_cassetto = {o["id_cassetto"]}")
        if "id_causaleprenotazione" in o:
            data.append(f"id_causaleprenotazione = {o["id_causaleprenotazione"]}")
        
        tmp = []
        for i in range(len(data)):
            tmp.append(data[i])
            tmp.append(', ')

        query = c.concatenate(tmp)
        print(query[:-2])
        return query[:-2]

    def validate(self):
        data = {}

        if self.timestamp_start         : data['timestamp_start']               = self.timestamp_start
        else                            : data['timestamp_start']               = None
        if self.timestamp_end           : data['timestamp_end']                 = self.timestamp_end
        else                            : data['timestamp_end']                 = None
        if self.waybill                 : data['waybill']                       = self.waybill
        else                            : data['waybill']                       = None
        if self.ticket                  : data['ticket']                        = self.ticket
        else                            : data['ticket']                        = None
        if self.id_utente               : data['id_utente']                     = self.id_utente
        else                            : data['id_utente']                     = None
        if self.id_locker               : data['id_locker']                     = self.id_locker
        else                            : data['id_locker']                     = None
        if self.id_cassetto             : data['id_cassetto']                   = self.id_cassetto
        else                            : data['id_cassetto']                   = None
        if self.id_causaleprenotazione  : data['id_causaleprenotazione']        = self.id_causaleprenotazione
        else                            : data['id_causaleprenotazione']        = None

        return data

