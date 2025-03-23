"""
Manager of Locker data
"""

from .. import crypt as c

class Locker():
    def __init__(self, args = None):
        if args is None:
            self.id             = None
            self.number         = None
            self.localita       = None
            self.id_azienda     = None
            self.status         = None
        else:
            self.id             = args.get("id")
            self.number         = args.get("number")
            self.localita       = args.get("localita")
            self.id_azienda     = args.get("id_azienda")
            self.status         = args.get("status")
    
    def json(self):
        data = {}
        if self.id:         data['id']          = self.id
        if self.number:     data['number']      = self.number
        if self.localita:   data['localita']    = self.localita
        if self.id_azienda: data['id_azienda']  = self.id_azienda
        if self.status:     data['status']      = self.status

        return data

    def base(self):
        return {
            "number" : 0,
            "localita" : 0,
            "id_azienda" : 0,
            "status" : ""
        }
    
    def query(self, o):
        data = []
        
        if "number" in o:
            data.append(f"number = {o['number']}")
        if "localita" in o:
            data.append(f"localita = {o['localita']}")
        if "id_azienda" in o:
            data.append(f"id_azienda = {o['id_azienda']}")
        if "status" in o:
            data.append(f"status = \'{o['status']}\'")

        tmp = []
        for i in range(len(data)):
            tmp.append(data[i])
            tmp.append(', ')

        query = c.concatenate(tmp)
        print(query[:-2])
        return query[:-2]