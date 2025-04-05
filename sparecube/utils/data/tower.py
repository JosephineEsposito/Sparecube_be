"""
Manager of Tower data
"""

from .. import crypt as c

class Tower():
    def __init__(self, args = None):
        if args is None:
            self.id             = None
            self.id_locker     = None
            self.number        = None
        else:
            self.id             = args.get("id")
            self.id_locker      = args.get("id_locker")
            self.number         = args.get("number")
    
    def json(self):
        data = {}
        if self.id:         data['id']          = self.id
        if self.id_locker:  data['id_locker']   = self.id_locker
        if self.number:     data['number']      = self.number

        return data

    def base(self):
        return {
            "localita" : 0,
            "id_locker" : 0,
            "number" : 0,
        }
    
    def query(self, o):
        data = []
        
        if "localita" in o:
            data.append(f"localita = {o['localita']}")
        if "id_locker" in o:
            data.append(f"id_locker = {o['id_locker']}")
        if "number" in o:
            data.append(f"number = {o['number']}")

        tmp = []
        for i in range(len(data)):
            tmp.append(data[i])
            tmp.append(', ')

        query = c.concatenate(tmp)
        print(query[:-2])
        return query[:-2]