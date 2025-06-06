"""
Manager of Drawer data
"""

from .. import crypt as c

class Drawer():
    def __init__(self, args = None):
        if args is None:
            # default values for attributes if args is not provided
            self.id         = None
            self.width      = None
            self.height     = None
            self.depth      = None
            self.status     = None
            self.id_torre   = None
            self.id_box     = None
        else:
            # initialize attributes with values from args dictionary
            self.id         = args.get('id')
            self.width      = args.get('width')
            self.height     = args.get('height')
            self.depth      = args.get('depth')
            self.status     = args.get('status')
            self.id_torre   = args.get('id_torre')
            self.id_box     = args.get('id_box')
    

    def json(self):
        data = {}

        if self.id          : data['id']            = self.id
        if self.id_torre    : data['id_torre']      = self.id_torre
        if self.id_box      : data['id_box']        = self.id_box
        if self.width       : data['width']         = self.width
        if self.height      : data['height']        = self.height
        if self.depth       : data['depth']         = self.depth
        if self.status      : data['status']        = self.status

        return data
    
    def clean(self):
        self.id         = None
        self.width      = None
        self.height     = None
        self.depth      = None
        self.status     = None
        self.id_torre   = None

    def base(self):
        return {
            "width" : 0,
            "height" : 0,
            "depth" : 0,
            "status" : "",
            "id_torre" : 0
        }
    
    def query(self, o):
        data = []

        if "width" in o:
            data.append(f"width = {o['width']}")
        if "height" in o:
            data.append(f"height = {o['height']}")
        if "depth" in o:
            data.append(f"depth = {o['depth']}")
        if "status" in o:
            data.append(f"status = \'{o['status']}\'")
        if "id_torre" in o:
            data.append(f"id_torre = {o['id_torre']}")

        tmp = []
        for i in range(len(data)):
            tmp.append(data[i])
            tmp.append(', ')

        query = c.concatenate(tmp)
        print(query[:-2])
        return query[:-2]
