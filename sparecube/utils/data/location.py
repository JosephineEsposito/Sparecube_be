"""
Manager of Location data
"""

from .. import crypt as c


class Location():
    def __init__(self, args = None):
        if args is None:
            self.id             = None
            self.name           = None
            self.road           = None
            self.city           = None
            self.civicnumber    = None
            self.postalcode     = None
            self.id_azienda     = None
            self.lat            = None
            self.lng            = None
            self.lockers        = []
        else:
            self.id             = args.get("id")
            self.name           = args.get("name")
            self.road           = args.get("road")
            self.city           = args.get("city")
            self.civicnumber    = args.get("civicnumber")
            self.postalcode     = args.get("postalcode")
            self.id_azienda     = args.get("id_azienda")
            self.lat            = args.get("lat")
            self.lng            = args.get("lng")
            self.lockers        = args.get("lockers", [])

    def json(self):
        data = {}
        if self.id:             data['id']          = self.id
        if self.name:           data['name']        = self.name
        if self.road:           data['road']        = self.road
        if self.city:           data['city']        = self.city
        if self.civicnumber:    data['civicnumber'] = self.civicnumber
        if self.postalcode:     data['postalcode']  = self.postalcode
        if self.id_azienda:     data['id_azienda']  = self.id_azienda

        if self.lockers:
            data['lockers'] = self.lockers

        if self.lat and self.lng:
             geometry = {}

             geometry['lat'] = self.lat
             geometry['lng'] = self.lng

             data['geometry'] = geometry
        else:
             geometry = {}

             geometry['lat'] = 41.0
             geometry['lng'] = 14.0

             data['geometry'] = geometry


        return data

    def base(self):
        return {
            "name" : "",
            "road" : "",
            "city" : "",
            "civicnumber" : "",
            "postalcode" : "",
            "id_azienda" : "",
            "lat" : 0.0,
            "lng" : 0.0
        }
    
    def query(self, o):
        data = []

        if "id" in o:
            data.append(f"id = {o['id']}")
        if "name" in o:
            data.append(f"name = \'{o['name']}\'")
        if "road" in o:
            data.append(f"road = \'{o['road']}\'")
        if "city" in o:
            data.append(f"city = {o['city']}")
        if "civicnumber" in o:
            data.append(f"civicnumber = {o['civicnumber']}")
        if "postalcode" in o:
            data.append(f"postalcode = {o['postalcode']}")
        if "id_azienda" in o:
            data.append(f"id_azienda = {o['id_azienda']}")
        if "lat" in o:
            data.append(f"lat = {o['lat']}")
        if "lng" in o:
            data.append(f"lng = {o['lng']}")

        tmp = []
        for i in range(len(data)):
            tmp.append(data[i])
            tmp.append(', ')

        query = c.concatenate(tmp)
        print(query[:-2])
        return query[:-2]
