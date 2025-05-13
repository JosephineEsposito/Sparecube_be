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
            self.city                       = None
            self.road                       = None
            self.id_utente                  = None
            self.id_locker                  = None
            self.id_torre                   = None
            self.id_cassetto                = None
            self.id_causaleprenotazione     = None
            self.operation_type             = None
            self.id_supervisor              = None
            self.SDA_Code                   = None
        else:
            # initialize attributes with values from args dictionary (from database)
            self.timestamp_start            = args.get('timestamp_start')
            self.timestamp_end              = args.get('timestamp_end')
            self.waybill                    = args.get('waybill')
            self.ticket                     = args.get('ticket')
            self.city                       = args.get('city')
            self.road                       = args.get('road')
            self.id_utente                  = args.get('id_utente')
            self.id_locker                  = args.get('id_locker')
            self.id_torre                   = args.get('id_torre')
            self.id_cassetto                = args.get('id_cassetto')
            self.id_causaleprenotazione     = args.get('id_causaleprenotazione')
            self.operation_type             = args.get('operation_type')
            self.id_supervisor              = args.get('id_supervisor')
            self.SDA_Code                   = args.get('SDA_Code')
    
    def json(self):
        data = {}

        if self.timestamp_start         : data['timestamp_start']               = self.timestamp_start
        if self.timestamp_end           : data['timestamp_end']                 = self.timestamp_end
        if self.waybill                 : data['waybill']                       = self.waybill
        if self.city                    : data['city']                          = self.city
        if self.road                    : data['road']                          = self.road
        if self.ticket                  : data['ticket']                        = self.ticket
        if self.id_utente               : data['id_utente']                     = self.id_utente
        if self.id_locker               : data['id_locker']                     = self.id_locker
        if self.id_torre                : data['id_torre']                      = self.id_torre
        if self.id_cassetto             : data['id_cassetto']                   = self.id_cassetto
        if self.id_causaleprenotazione  : data['id_causaleprenotazione']        = self.id_causaleprenotazione
        if self.operation_type          : data['operation_type']                = self.operation_type
        if self.id_supervisor           : data['id_supervisor']                 = self.id_supervisor
        if self.SDA_Code                : data['SDA_Code']                      = self.SDA_Code
        else                            : data['SDA_Code']                      = None

        return data
    
    def clean(self):
        self.timestamp_start            = None
        self.timestamp_end              = None
        self.waybill                    = None
        self.ticket                     = None
        self.id_utente                  = None
        self.id_locker                  = None
        self.id_torre                   = None
        self.id_cassetto                = None
        self.id_causaleprenotazione     = None
        self.operation_type             = None
        self.id_supervisor              = None
        self.SDA_Code                   = None

    def base(self):
        return {
            "timestamp_start" : "0000-00-00",
            "timestamp_end" : "0000-00-00",
            "waybill" : "",
            "ticket" : "",
            "id_utente" : 0,
            "id_locker" : 0,
            "id_torre" : 0,
            "id_cassetto" : 0,
            "id_causaleprenotazione" : 0,
            "operation_type" : 0,
            "id_supervisor" : 0,
            "SDA_Code" : ""
        }
    
    def query(self, o):
        data = []
        if "waybill" in o:
            data.append(f"waybill = {o['waybill']}")
        if "ticket" in o:
            data.append(f"ticket = {o['ticket']}")
        if "id_utente" in o:
            data.append(f"id_utente = {o['id_utente']}")
        if "id_locker" in o:
            data.append(f"id_locker = {o['id_locker']}")
        if "id_torre" in o:
            data.append(f"id_torre = {o['id_torre']}")
        if "id_cassetto" in o:
            data.append(f"id_cassetto = {o['id_cassetto']}")
        if "id_causaleprenotazione" in o:
            data.append(f"id_causaleprenotazione = \'{o['id_causaleprenotazione']}\'")
            if o['id_causaleprenotazione'] == 'CLOSED' or o['id_causaleprenotazione'] == 'CANCELLED' or o['id_causaleprenotazione'] == 'FAILED':
                data.append(f"timestamp_end = \'{c.get_date()}\'")
        if "operation_type" in o:
            data.append(f"operation_type = {o['operation_type']}")

        if "id_supervisor" in o:
            data.append(f"id_supervisor = {o['id_supervisor']}")
        if "SDA_Code" in o:
            data.append(f"SDA_Code = \'{o['SDA_Code']}\'")
        
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
        if self.id_torre                : data['id_torre']                      = self.id_torre
        else                            : data['id_torre']                      = None
        if self.id_cassetto             : data['id_cassetto']                   = self.id_cassetto
        else                            : data['id_cassetto']                   = None
        if self.id_causaleprenotazione  : data['id_causaleprenotazione']        = self.id_causaleprenotazione
        else                            : data['id_causaleprenotazione']        = None
        if self.operation_type          : data['operation_type']                = self.operation_type
        else                            : data['operation_type']                = None
        if self.id_supervisor           : data['id_supervisor']                 = self.id_supervisor
        else                            : data['id_supervisor']                 = None
        if self.SDA_Code                : data['SDA_Code']                      = self.SDA_Code
        else                            : data['SDA_Code']                      = None
        return data

