"""
Manager of Logs data for the database
"""

from .. import crypt as c

class Log():
    def __init__(self, args = None):
        if args is None:
            # default values for attributes if args is not provided
            self.timestamp          = None
            self.event              = None
            self.id_prenotazione    = None
            self.id_utente          = None
            self.id_locker          = None
        else:
            # initialize attributes with values from args dictionary
            self.timestamp          = c.get_time()
            self.event              = args.get('event')
            self.id_prenotazione    = args.get('id_prenotazione')
            self.id_utente          = None
            self.id_locker          = None
    

    def json(self):
        log = {}

        if self.timestamp       : log['timestamp']          = self.timestamp
        if self.event           : log['event']              = self.event
        if self.id_prenotazione : log['id_prenotazione']    = self.id_prenotazione
        else                    : log['id_prenotazione']    = None
        if self.id_utente       : log['id_utente']          = self.id_utente
        else                    : log['id_utente']          = None
        if self.id_locker       : log['id_locker']          = self.id_locker
        else                    : log['id_locker']          = None

        return log
    
    def clean(self):
            self.timestamp          = None
            self.event              = None
            self.id_prenotazione    = None
            self.id_utente          = None
            self.id_locker          = None

    def base(self):
        return {
             "timestamp" : 0,
             "event" : "",
             "id_prenotazione" : 0,
             "id_utente" : 0,
             "id_locker" : 0
        }
    
    def validate(self):
        log = {}

        if self.timestamp       : log['timestamp']          = self.timestamp
        else                    : log['timestamp']          = c.get_date()#time(timelim=1_000_000)
        if self.event           : log['event']              = self.event
        else                    : log['timestamp']          = None
        if self.id_prenotazione : log['id_prenotazione']    = self.id_prenotazione
        else                    : log['id_prenotazione']    = None
        if self.id_utente       : log['id_utente']          = self.id_utente
        else                    : log['id_utente']          = None
        if self.id_locker       : log['id_locker']          = self.id_locker
        else                    : log['id_locker']          = None

        return log