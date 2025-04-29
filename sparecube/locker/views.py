#region | IMPORTS
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from account.serializers import UserSerializer


# for DB
import pyodbc


# for encrypting
from utils import crypt as c
# for output response
from utils import output as o
# for database connection
from utils import database as db
# for Localita
from utils.data import location
# for Locker
from utils.data import locker
# for Torre
from utils.data import tower 
# for Cassetto
from utils.data import drawer
# for Prenotazione
from utils.data import booking
# for Logs
from utils.data import log
# for MQTT
from locker.mqttMsg import To_Lockers_MSGs
from utils.MQTT import mqtt_obj, MQTT_MSG, Topics
import logging

#endregion



# ====================.====================.====================.====================.==================== #
#region | Custom functions and global variables
# ====================. GLOBAL VARIABLES .==================== #

RES = o.Output() # Formato per ritornare i dati
logger = logging.getLogger(__name__) # Add Log in console to monitor the MQTT Connection

#endregion
# ====================.====================.====================.====================.==================== #


# ====================.====================.====================.====================.==================== #
#region | Localita
"""
Class to manage Localita
GET     - single (self) location info
GET     - all locations infos
PUT     - update single location info
DELETE  - delete (id) location info
"""
class LocationAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get(self, request, id):
        # ritorna le informazioni di una localita
        RES.clean()

        #database connection
        connection = db.connectDB()
        if connection['esito'] == -1:
            RES.dbError()
            RES.setErrors(str(connection['connection']))
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()

        #query
        try:
            cursor.execute(f"select * from Localita where id = {id}")
            res = cursor.fetchone()

            if res:
                cols = [cols[0] for cols in cursor.description]
                LOC = location.Location(dict(zip(cols, res)))
            cursor.close()
            connection['connection'].close()

            RES.setData(LOC.json())

        except pyodbc.Error as err:
            RES.dbError()
            RES.setErrors(str(err))

        return Response(RES.json(), status=status.HTTP_200_OK)
    
    def put(self, request):
        # per aggiornare le informazioni di una localita
        RES.clean()
        serializer = self.serializer_class(request.user)
        user = serializer.data
        rLocalita = request.data

        #permissions
        if user["account_type"] != 'ADMIN': # solo per amministratori
            RES.permissionDenied()
            return Response(RES.json(), status=status.HTTP_200_OK)
        
        #database connection
        connection = db.connectDB()
        if connection['esito'] == -1:
            RES.dbError()
            RES.setErrors(connection['connection'])
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()

        #we check if the location exists in our database
        cursor.execute(f"select * from Localita where id = {rLocalita['id']}")
        res = cursor.fetchone()
        if not res:
            RES.setMessage("La località che si vuole modificare non esiste.")
            return Response(RES.json(), status=status.HTTP_200_OK)
        
        query_s = 'update Localita set '
        query_e = f" where id = {rLocalita['id']}"
        localita = location.Location()
        values = localita.query(rLocalita)

        query = c.concatenate([query_s, values, query_e])
        print(query)

        try:
            cursor.execute(query)
            cursor.commit()
            cursor.close()
            connection['connection'].close()
            RES.setMessage('Località aggiornata con successo.')
        except pyodbc.Error as err:
            RES.dbError()
            RES.setErrors(str(err))

        return Response(RES.json(), status=status.HTTP_200_OK)
    
    def post(self, request):
        # per aggiungere nuove localita
        RES.clean()
        serializer = self.serializer_class(request.user)
        user = serializer.data
        rLocalita = request.data

        #permissions
        if user["account_type"] != 'ADMIN': # solo per amministratori
            RES.permissionDenied()
            return Response(RES.json(), status=status.HTTP_200_OK)
        
        #database connection
        connection = db.connectDB()
        if connection['esito'] == -1:
            RES.dbError()
            RES.setErrors(connection['connection'])
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()

        #variables
        db_localita = location.Location()
        db_localita = db_localita.base()

        #query
        cursor.execute('select * from Localita where name = ?', rLocalita['name'])
        res = cursor.fetchone()
        if res:
            RES.setMessage('Esiste già una località con questo id.')
            RES.setResult(-1)
            return Response(RES.json(), status=status.HTTP_200_OK)
        
        #verifying data
        if set(rLocalita.keys()) != set(db_localita.keys()):
            RES.setMessage('Mancano dati.')
            RES.setData({'nuovo' : rLocalita.keys(), 'vecchio' : db_localita.keys()})
            return Response(RES.json(), status=status.HTTP_200_OK)
        
        #we convert and check the values to the correct ones!
        loc = location.Location(rLocalita)
        """
        valid = loc.validate()
        if valid['esito'] == -1:
            RES.setMessage('L\'oggetto inviato non è valido.')
            RES.setData(valid)
            return Response(RES.json(), status=status.HTTP_200_OK)
        """
        
        #we insert the data into the database
        try:
            cursor.execute('''insert into Localita (name, road, city, civicnumber, postalcode, id_azienda, lat, lng)
                              values(?, ?, ?, ?, ?, ?, ?, ?)''', loc.name, loc.road, loc.city, loc.civicnumber, loc.postalcode, loc.id_azienda, loc.lat, loc.lng)
            
            cursor.commit()
            cursor.close()
            connection['connection'].close()
            RES.setResult(0)
            RES.setMessage('Località inserita.')
        
        except pyodbc.Error as err:
            RES.dbError()
            RES.setResult(-1)
            RES.setErrors(str(err))
        
        return Response(RES.json(), status=status.HTTP_200_OK)
    
    def delete(self,request, id):
        # per eliminare una localita
        RES.clean()
        serializer = self.serializer_class(request.user)
        user = serializer.data

        #permissions
        if user["account_type"] != 'ADMIN': # solo per amministratori
            RES.permissionDenied()
            return Response(RES.json(), status=status.HTTP_200_OK)
        
        #database connection
        connection = db.connectDB()
        if connection['esito'] == -1:
            RES.dbError()
            RES.setErrors(connection['connection'])
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()
        
        #query
        try:
            cursor.execute(f"delete Localita where id = {id}")
            cursor.commit()
            cursor.close()
            connection['connection'].close()
            RES.setMessage('Località eliminata con successo.')
        
        except pyodbc.Error as err:
            RES.dbError()
            RES.setErrors(str(err))
        
        return Response(RES.json(), status=status.HTTP_200_OK)

"""
Class to get all Locations data
GET     - get all data
"""
class LocationsAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get(self, request):
        # ritorna tutti i dettagli di tutte le locations
        RES.clean()
        serializer = self.serializer_class(request.user)
        user = serializer.data

        #permissions
        if user["account_type"] == 'USER': # solo per amministratori e operatori (limitato)
            RES.permissionDenied()
            return Response(RES.json(), status=status.HTTP_200_OK)

        #database connection
        connection = db.connectDB()
        if connection['esito'] == -1:
            RES.dbError()
            RES.setErrors(str(connection['connection']))
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()

        #query
        try:
            locations = []

            if user['account_type'] == 'OPERATOR':
                cursor.execute("SELECT id, name FROM Localita")
                res = cursor.fetchall()

                if res:
                    cols = [col[0] for col in cursor.description]
                    for row in res:
                        LOC = location.Location(dict(zip(cols, row)))
                        locations.append(LOC.json())

            else:
                # Amministratore: includi i locker
                cursor.execute("select L.*, LO.id as id_locker from Localita as L left join Locker as LO on L.id = LO.localita")
                res = cursor.fetchall()

                if res:
                    cols = [col[0] for col in cursor.description]
                    
                    # Raggruppa per ID località
                    grouped = {}
                    for row in res:
                        row_dict = dict(zip(cols, row))
                        loc_id = row_dict['id']

                        if loc_id not in grouped:
                            grouped[loc_id] = {
                                'id': row_dict['id'],
                                'name': row_dict['name'],
                                'road': row_dict['road'],
                                'city': row_dict['city'],
                                'civicnumber': row_dict.get('civicnumber'),
                                'postalcode': row_dict['postalcode'],
                                'id_azienda': row_dict.get('id_azienda'),
                                'lat': row_dict.get('lat'),
                                'lng': row_dict.get('lng'),
                                'lockers': []
                            }

                        if row_dict['id_locker'] is not None:
                            grouped[loc_id]['lockers'].append(row_dict['id_locker'])


                    # Crea oggetti Location
                    for loc_data in grouped.values():
                        LOC = location.Location(loc_data)
                        locations.append(LOC.json())

            cursor.close()
            connection['connection'].close()

            RES.setData(locations)

        except pyodbc.Error as err:
            RES.dbError()
            RES.setErrors(str(err))

        return Response(RES.json(), status=status.HTTP_200_OK)

#endregion
# ====================.====================.====================.====================.==================== #


# ====================.====================.====================.====================.==================== #
#region | Locker
"""
Class to manage Locker
GET     - single (id) locker info
PUT     - update single locker info
DELETE  - delete (id) locker info
"""
class LockerAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer
    
    def get(self, request, id):
        # ritorna le informazioni di un locker
        RES.clean()

        #database connection
        connection = db.connectDB()
        if connection['esito'] == -1:
            RES.dbError()
            RES.setErrors(str(connection['connection']))
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()

        #query
        try:
            cursor.execute(f"select * from Locker where id = {id}")
            res = cursor.fetchone()

            if res:
                cols = [cols[0] for cols in cursor.description]
                LOC = locker.Locker(dict(zip(cols, res)))
                RES.setData(LOC.json())
                RES.setResult(0)
            else:
                RES.setData({})
                RES.setResult(-1)
            cursor.close()
            connection['connection'].close()


        except pyodbc.Error as err:
            RES.dbError()
            RES.setErrors(str(err))

        return Response(RES.json(), status=status.HTTP_200_OK)
    
    def put(self, request):
        # per aggiornare le informazioni di un locker
        RES.clean()
        serializer = self.serializer_class(request.user)
        user = serializer.data
        rLocker = request.data

        #permissions
        if user["account_type"] != 'ADMIN': # solo per amministratori
            RES.permissionDenied()
            return Response(RES.json(), status=status.HTTP_200_OK)
        
        #database connection
        connection = db.connectDB()
        if connection['esito'] == -1:
            RES.dbError()
            RES.setErrors(connection['connection'])
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()

        #we check if the locker exists in our database
        cursor.execute(f"select * from Locker where id = {rLocker['id']}")
        res = cursor.fetchone()
        if not res:
            RES.setMessage("Il locker che si vuole modificare non esiste.")
            return Response(RES.json(), status=status.HTTP_200_OK)
        
        query_s = 'update Locker set '
        query_e = f" where id = {rLocker['id']}"
        locker_q = locker.Locker()
        values = locker_q.query(rLocker)

        query = c.concatenate([query_s, values, query_e])

        try:
            cursor.execute(query)
            cursor.commit()
            cursor.close()
            connection['connection'].close()
            RES.setMessage('Locker aggiornato con successo.')
        except pyodbc.Error as err:
            RES.dbError()
            RES.setErrors(str(err))

        return Response(RES.json(), status=status.HTTP_200_OK)
    
    def post(self, request):
        # per aggiungere nuovi locker
        RES.clean()
        serializer = self.serializer_class(request.user)
        user = serializer.data
        rLocker = request.data

        #permissions
        if user["account_type"] != 'ADMIN': # solo per amministratori
            RES.permissionDenied()
            return Response(RES.json(), status=status.HTTP_200_OK)
        
        #database connection
        connection = db.connectDB()
        if connection['esito'] == -1:
            RES.dbError()
            RES.setErrors(connection['connection'])
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()

        #variables
        db_locker = locker.Locker()
        db_locker = db_locker.base()

        #query
        cursor.execute(f"select * from Locker where number = {rLocker['number']}")
        res = cursor.fetchone()
        if res:
            RES.setMessage('Esiste già un locker con questo id.')
            RES.setResult(-1)
            return Response(RES.json(), status=status.HTTP_200_OK)
        
        #verifying data
        if set(rLocker.keys()) != set(db_locker.keys()):
            RES.setMessage('Mancano dati.')
            RES.setData({'nuovo' : rLocker.keys(), 'vecchio' : db_locker.keys()})
            return Response(RES.json(), status=status.HTTP_200_OK)
        
        #we convert and check the values to the correct ones!
        loc = locker.Locker(rLocker)
        """
        valid = loc.validate()
        if valid['esito'] == -1:
            RES.setMessage('L\'oggetto inviato non è valido.')
            RES.setData(valid)
            return Response(RES.json(), status=status.HTTP_200_OK)
        """
        
        #we insert the data into the database
        try:
            cursor.execute('''insert into Locker (number, localita, id_azienda, status)
                              values(?, ?, ?, ?)''', loc.number, loc.localita, loc.id_azienda, loc.status)
            
            cursor.commit()
            cursor.close()
            connection['connection'].close()
            RES.setResult(0)
            RES.setMessage('Locker inserito.')
        
        except pyodbc.Error as err:
            RES.dbError()
            RES.setResult(-1)
            RES.setErrors(str(err))
        
        return Response(RES.json(), status=status.HTTP_200_OK)
    
    def delete(self,request, id):
        # per eliminare un locker
        RES.clean()
        serializer = self.serializer_class(request.user)
        user = serializer.data

        #permissions
        if user["account_type"] != 'ADMIN': # solo per amministratori
            RES.permissionDenied()
            return Response(RES.json(), status=status.HTTP_200_OK)
        
        #database connection
        connection = db.connectDB()
        if connection['esito'] == -1:
            RES.dbError()
            RES.setErrors(connection['connection'])
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()
        
        #query cassetti
        try:
            cursor.execute(f"delete Cassetto where id_locker = {id}")
            cursor.commit()
            cursor.close()
            connection['connection'].close()
            RES.setMessage('Cassetti eliminati con successo.')
        except pyodbc.Error as err:
            RES.dbError()
            RES.setResult(-1)
            RES.setErrors(str(err))
            return Response(RES.json(), status=status.HTTP_200_OK)

        #database connection
        connection = db.connectDB()
        if connection['esito'] == -1:
            RES.dbError()
            RES.setErrors(connection['connection'])
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()

        #query locker
        try:
            cursor.execute(f"delete Locker where id = {id}")
            cursor.commit()
            cursor.close()
            connection['connection'].close()
            RES.setMessage('Locker eliminato con successo.')
        
        except pyodbc.Error as err:
            RES.dbError()
            RES.setErrors(str(err))
        
        return Response(RES.json(), status=status.HTTP_200_OK)


"""
Class to get all Lockers data
GET     - get all data
"""
class LockersAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get(self, request):
        #ritorna tutte le informazioni di tutti i locker
        RES.clean()
        serializer = self.serializer_class(request.user)
        user = serializer.data

        #permissions
        if user["account_type"] == 'USER': # solo per amministratori e operatori (limitato)
            RES.permissionDenied()
            return Response(RES.json(), status=status.HTTP_200_OK)

        #database connection
        connection = db.connectDB()
        if connection['esito'] == -1:
            RES.dbError()
            RES.setErrors(str(connection['connection']))
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()

        #query
        try:
            lockers = []
            if user['account_type'] == 'OPERATOR':
                cursor.execute("select id, localita from Locker")
            else:
                cursor.execute("select L.id, LO.name as localita, L.id_azienda, L.status from Locker as L, Localita as LO where L.localita = LO.id")
            res = cursor.fetchall()

            if res:
                cols = [cols[0] for cols in cursor.description]
                for row in res:
                    LOC = locker.Locker(dict(zip(cols, row)))
                    lockers.append(LOC.json())
            cursor.close()
            connection['connection'].close()

            RES.setData(lockers)
        
        except pyodbc.Error as err:
            RES.dbError()
            RES.setErrors(str(err))

        return Response(RES.json(), status=status.HTTP_200_OK)


#endregion
# ====================.====================.====================.====================.==================== #


# ====================.====================.====================.====================.==================== #
#region | Torre
"""
Class to manage Torre
GET     - single (id) tower info
PUT     - update single tower info
DELETE  - delete (id) tower info
"""
class TowerAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer
    
    def get(self, request, id):
        # ritorna le informazioni di una torre
        RES.clean()

        #database connection
        connection = db.connectDB()
        if connection['esito'] == -1:
            RES.dbError()
            RES.setErrors(str(connection['connection']))
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()

        #query
        try:
            cursor.execute(f"select * from Torre where id = {id}")
            res = cursor.fetchone()

            if res:
                cols = [cols[0] for cols in cursor.description]
                TOW =  tower.Tower(dict(zip(cols, res)))
            cursor.close()
            connection['connection'].close()

            RES.setData(TOW.json())

        except pyodbc.Error as err:
            RES.dbError()
            RES.setErrors(str(err))

        return Response(RES.json(), status=status.HTTP_200_OK)
    
    def put(self, request):
        # per aggiornare le informazioni di un torre
        RES.clean()
        serializer = self.serializer_class(request.user)
        user = serializer.data
        rTower = request.data

        #permissions
        if user["account_type"] != 'ADMIN': # solo per amministratori
            RES.permissionDenied()
            return Response(RES.json(), status=status.HTTP_200_OK)
        
        #database connection
        connection = db.connectDB()
        if connection['esito'] == -1:
            RES.dbError()
            RES.setErrors(connection['connection'])
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()

        #we check if the locker exists in our database
        cursor.execute(f"select * from Torre where id = {rTower['id']}")
        res = cursor.fetchone()
        if not res:
            RES.setMessage("La torre che si vuole modificare non esiste.")
            return Response(RES.json(), status=status.HTTP_200_OK)
        
        query_s = 'update Locker set '
        query_e = f" where id = {rTower['id']}"
        tower_q = tower.Tower()
        values = tower_q.query(rTower)

        query = c.concatenate([query_s, values, query_e])

        try:
            cursor.execute(query)
            cursor.commit()
            cursor.close()
            connection['connection'].close()
            RES.setMessage('Torre aggiornata con successo.')
        except pyodbc.Error as err:
            RES.dbError()
            RES.setErrors(str(err))

        return Response(RES.json(), status=status.HTTP_200_OK)


"""
Class to get all Lockers data
GET     - get all data
"""
class TowersAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get(self, request):
        #ritorna tutte le informazioni di tutti le torri
        RES.clean()
        serializer = self.serializer_class(request.user)
        user = serializer.data

        #permissions
        if user["account_type"] == 'USER': # solo per amministratori e operatori (limitato)
            RES.permissionDenied()
            return Response(RES.json(), status=status.HTTP_200_OK)

        #database connection
        connection = db.connectDB()
        if connection['esito'] == -1:
            RES.dbError()
            RES.setErrors(str(connection['connection']))
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()

        #query
        try:
            towers = []
            if user['account_type'] == 'OPERATOR':
                cursor.execute("select * from Torre")
            else:
                cursor.execute("select * from Torre")
            res = cursor.fetchall()

            if res:
                cols = [cols[0] for cols in cursor.description]
                for row in res:
                    TOW = tower.Tower(dict(zip(cols, row)))
                    towers.append(TOW.json())
            cursor.close()
            connection['connection'].close()

            RES.setData(towers)
        
        except pyodbc.Error as err:
            RES.dbError()
            RES.setErrors(str(err))

        return Response(RES.json(), status=status.HTTP_200_OK)

#endregion
# ====================.====================.====================.====================.==================== #


# ====================.====================.====================.====================.==================== #
#region | Cassetto
"""
Class to manage Cassetto
GET     - single (id) drawer info
PUT     - update single drawer info
POST    - add new drawer
DELETE  - delete (id) drawer info
"""
class DrawerAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get(self, request, id):
        # ritorna le informazioni di un cassetto
        RES.clean()

        #database connection
        connection = db.connectDB()
        if connection['esito'] == -1:
            RES.dbError()
            RES.setErrors(str(connection['connection']))
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()

        #query
        drawers = []
        try:
            cursor.execute(f"select * from Cassetto where id = {id}")
            res = cursor.fetchone()

            if res:
                cols = [cols[0] for cols in cursor.description]
                DRA = drawer.Drawer(dict(zip(cols, res)))
            cursor.close()
            connection['connection'].close()

            RES.setData(DRA.json())

        except pyodbc.Error as err:
            RES.dbError()
            RES.setErrors(str(err))

        return Response(RES.json(), status=status.HTTP_200_OK)
    
    def put(self, request):
        RES.clean()
        # per aggiornare le informazioni di un cassetto
        serializer = self.serializer_class(request.user)
        user = serializer.data
        rDrawer = request.data

        #permissions
        if user["account_type"] != 'ADMIN': # solo per amministratori?
            RES.permissionDenied()
            return Response(RES.json(), status=status.HTTP_200_OK)
        
        #database connection
        connection = db.connectDB()
        if connection['esito'] == -1:
            RES.dbError()
            RES.setErrors(connection['connection'])
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()

        #we check if the locker exists in our database
        cursor.execute(f"select * from Cassetto where id = {rDrawer['id']}")
        res = cursor.fetchone()
        if not res:
            RES.setMessage("Il cassetto che si vuole modificare non esiste.")
            return Response(RES.json(), status=status.HTTP_200_OK)
        
        query_s = 'update Cassetto set '
        query_e = f" where id = {rDrawer['id']}"
        drawer_q = drawer.Drawer()
        values = drawer_q.query(rDrawer)

        query = c.concatenate([query_s, values, query_e])

        try:
            cursor.execute(query)
            cursor.commit()
            cursor.close()
            connection['connection'].close()
            RES.setMessage('Cassetto aggiornato con successo.')
        except pyodbc.Error as err:
            RES.dbError()
            RES.setErrors(str(err))

        return Response(RES.json(), status=status.HTTP_200_OK)

    def post(self, request):
        # per aggiungere nuovi cassetti
        RES.clean()
        serializer = self.serializer_class(request.user)
        user = serializer.data
        rDrawer = request.data

        #permissions
        if user['account_type'] != 'ADMIN': #solo per amministratori
            RES.permissionDenied()
            return Response(RES.json(), status=status.HTTP_200_OK)
        
        #database connection
        connection = db.connectDB()
        if connection['esito'] == -1:
            RES.dbError()
            RES.setErrors(connection['connection'])
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()

        #variables
        db_drawer = drawer.Drawer()
        db_drawer = db_drawer.base()

        
        #verifying data
        if set(rDrawer.keys()) != set(db_drawer.keys()):
            RES.setMessage('Mancano dati.')
            RES.setData({'nuovo' : rDrawer.keys(), 'vecchio' : db_drawer.keys()})
            return Response(RES.json(), status=status.HTTP_200_OK)
        
        dra = drawer.Drawer(rDrawer)
        #we insert the data into the database
        try:
            cursor.execute('''insert into Cassetto (id_locker, width, height, depth, status)
                              values(?, ?, ?, ?, ?)''', dra.id_locker, dra.width, dra.height, dra.depth, dra.status)
            
            cursor.commit()
            cursor.close()
            connection['connection'].close()
            RES.setResult(0)
            RES.setMessage('Cassetto inserito.')
        
        except pyodbc.Error as err:
            RES.dbError()
            RES.setResult(-1)
            RES.setErrors(str(err))
        
        return Response(RES.json(), status=status.HTTP_200_OK)
    
    def delete(self,request, id):
        # per eliminare un cassetto
        RES.clean()
        serializer = self.serializer_class(request.user)
        user = serializer.data

        if user['account_type'] != 'ADMIN': #amministratore only?
            RES.permissionDenied()
            return Response(RES.json(), status=status.HTTP_200_OK)
        
        #database connection
        connection = db.connectDB()
        if connection['esito'] == -1:
            RES.dbError()
            RES.setErrors(connection['connection'])
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()
        
        #query cassetti
        try:
            cursor.execute(f"delete Cassetto where id = {id}")
            cursor.commit()
            cursor.close()
            connection['connection'].close()
            RES.setMessage('Cassetto eliminato con successo.')

        except pyodbc.Error as err:
            RES.dbError()
            RES.setResult(-1)
            RES.setErrors(str(err))
        
        return Response(RES.json(), status=status.HTTP_200_OK)


"""
Class to get all Drawers data
GET     - get all data
"""
class DrawersAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get(self, request):
        # ritorna tutte le informazioni di tutti i cassetti
        RES.clean()
        serializer = self.serializer_class(request.user)
        user = serializer.data

        #permissions
        if user['account_type'] == 'USER': #solo per amministratori e operatori (limitato)
            RES.permissionDenied()
            return Response(RES.json(), status=status.HTTP_200_OK)

        #database connection
        connection = db.connectDB()
        if connection['esito'] == -1:
            RES.dbError()
            RES.setErrors(str(connection['connection']))
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()

        #query
        try:
            drawers = []
            if user['account_type'] == 'OPERATOR':
                cursor.execute("select id, id_locker from Cassetto")
            else:
                cursor.execute("select * from Cassetto")
            res = cursor.fetchall()

            if res:
                cols = [cols[0] for cols in cursor.description]
                for row in res:
                    DRA = drawer.Drawer(dict(zip(cols, row)))
                    drawers.append(DRA.json())
            cursor.close()
            connection['connection'].close()

            RES.setData(drawers)
        
        except pyodbc.Error as err:
            RES.dbError()
            RES.setErrors(str(err))

        return Response(RES.json(), status=status.HTTP_200_OK)


"""
Class to get all Drawers data filtered by status
GET    - get all data by status
"""
class DrawerFiltered(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get(self, request):
        # ritorna tutte le informazioni di tutti i cassetti filtrati per status
        RES.clean()
        serializer = self.serializer_class(request.user)
        user = serializer.data

        #permissions
        if user['account_type'] == 'USER': #solo per amministratori e operatori (limitato)
            RES.permissionDenied()
            return Response(RES.json(), status=status.HTTP_200_OK)

        #database connection
        connection = db.connectDB()
        if connection['esito'] == -1:
            RES.dbError()
            RES.setErrors(str(connection['connection']))
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()

        #query
        try:
            drawers = []
            cursor.execute("""
                WITH LatestPrenotazione AS (
                    SELECT p.*,
                        ROW_NUMBER() OVER (PARTITION BY p.id_cassetto ORDER BY p.timestamp_start DESC, p.timestamp_start DESC) AS rn
                    FROM Prenotazione p
                )
                SELECT 
                    t.id_locker,
                    c.id,
                    c.id_torre, 
                    c.id_box, 
                    c.width, 
                    c.height, 
                    c.depth, 
                    c.status, 
                    c.is_full, 
                    c.is_open
                FROM Torre AS t
                JOIN Cassetto c ON c.id_torre = t.id
                JOIN Locker l ON t.id_locker = l.id
                LEFT JOIN LatestPrenotazione p ON p.id_cassetto = c.id AND p.rn = 1
                WHERE p.id_cassetto IS NULL OR p.id_causaleprenotazione != 'OPEN'
            """)

            res = cursor.fetchall()

            if res:
                cols = [cols[0] for cols in cursor.description]
                for row in res:
                    DRA = drawer.Drawer(dict(zip(cols, row)))
                    drawers.append(DRA.json())
            cursor.close()
            connection['connection'].close()

            RES.setData(drawers)
        
        except pyodbc.Error as err:
            RES.dbError()
            RES.setErrors(str(err))

        return Response(RES.json(), status=status.HTTP_200_OK)


#endregion
# ====================.====================.====================.====================.==================== #


# ====================.====================.====================.====================.==================== #
#region | Prenotazioni
"""
Class to manage Prenotazioni
GET     - all booking infos
PUT     - update single booking info
POST    - add new booking info
DELETE  - delete (id) booking info
"""
class BookingAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get(self, request, id):
        # ritorna le informazioni di una prenotazione
        serializer = self.serializer_class(request.user)
        user = serializer.data
        RES.clean()

        #permissions
        if user["account_type"] != 'ADMIN': # solo per amministratori
            RES.permissionDenied()
            return Response(RES.json(), status=status.HTTP_200_OK)

        #database connection
        connection = db.connectDB()
        if connection['esito'] == -1:
            RES.dbError()
            RES.setErrors(str(connection['connection']))
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()

        #query
        try:
            cursor.execute(f"select * from Prenotazione where timestamp_start = {id}")
            res = cursor.fetchone()

            if res:
                cols = [cols[0] for cols in cursor.description]
                BOO = booking.Booking(dict(zip(cols, res)))
            cursor.close()
            connection['connection'].close()

            RES.setData(BOO.json())

        except pyodbc.Error as err:
            RES.dbError()
            RES.setErrors(str(err))

        return Response(RES.json(), status=status.HTTP_200_OK)

    def put(self, request):
        # per aggiornare le informazioni di una prenotazione
        RES.clean()
        serializer = self.serializer_class(request.user)
        user = serializer.data
        rBooking = request.data


        # permissions
        if user["account_type"] != 'OPERATOR':  # solo per amministratori?

        #permissions
        if user["account_type"] != 'OPERATOR': # solo per amministratori?

            RES.permissionDenied()
            return Response(RES.json(), status=status.HTTP_200_OK)

        # database connection
        connection = db.connectDB()
        if connection['esito'] == -1:
            RES.dbError()
            RES.setErrors(connection['connection'])
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()


        # # We need to save backup of this reservation to manage failed publishing mqtt msg
        # # region Reservation Backup
        # cursor.execute('select * from Prenotazione where timestamp_start = ?', (rBooking['timestamp_start']))
        # res = cursor.fetchone()
        # if not res:
        #     RES.setMessage("La prenotazione che si vuole modificare non esiste.")
        #     return Response(RES.json(), status=status.HTTP_200_OK)
        # cols = [cols[0] for cols in cursor.description]
        # BOOTemp = booking.Booking(dict(zip(cols, res)))
        # status_temp = BOOTemp.id_causaleprenotazione
        # timestamp_start_temp = BOOTemp.timestamp_start
        # # endregion


        # we check if the locker exists in our database

        #we check if the locker exists in our database

        query = f"select p.id_locker, p.waybill, p.ticket, p.id_causaleprenotazione, c.id_torre, c.id_box from Prenotazione p, Cassetto c where timestamp_start = \'{rBooking['timestamp_start']}\' and p.id_cassetto = c.id"
        cursor.execute(query)
        res = cursor.fetchone()
        if not res:
            RES.setMessage("La prenotazione che si vuole modificare non esiste.")
            return Response(RES.json(), status=status.HTTP_200_OK)
        else:
            cols = [cols[0] for cols in cursor.description]
            BOO = (dict(zip(cols, res)))


        prenot = BOO.copy()

        # Author: @josephineesposito - 27042025
        # AGGIUNTA STRUTTURA MESSAGGIO MQTT
        # Batoul..
        # Move forming MQTT Msg to mqttMsg class
        # Make the reservation status updated to the new status if only the mqtt msg published successfully.


        prenot = BOO.copy()
       
        mqtt_data = {
            "Producer": "Sparecube_Website",
            "Message": "cancel_reservation",
            "DateTime": timestamp_message,
            "Message_Id": "Sparecube_Website:cancel_reservation:" + timestamp_message,
            "data": {
                "idTower": prenot['id_torre'],
                "myBox": {
                    "id": prenot['id_box'],
                    "letteraVettura": prenot['waybill'],
                    "ticket": prenot['ticket'],
                    "statoPrenotazione": BOO['id_causaleprenotazione']
                }
            }
        }

        print(mqtt_data)

        mqtt_msg = MQTT_MSG(
            topic=Topics.ToLocker.uniqueLocker + str(BOO['id_locker']),
            payload=mqtt_data
        )

        mqtt_obj.connect()

        if mqtt_obj.connected:
            mqtt_obj.publish_msg(mqtt_msg)

        if not mqtt_obj.connected or not mqtt_obj.published:
            if not mqtt_obj.connected:
                logger.warning("MQTT NOT CONNECTED")
            if not mqtt_obj.published:
                logger.warning("MQTT MSG NOT PUBLISHED")

            try:
                cursor.execute(
                    '''UPDATE Prenotazione SET id_causaleprenotazione = 'FAILED' and timestamp_end = ? WHERE timestamp_start = ?''',
                    c.get_date(), rBooking['timestamp_start'])
                cursor.commit()
            except pyodbc.Error as err:
                RES.dbError()
                RES.setErrors(str(err))
        
        query_s = 'update Prenotazione set '
        query_e = f" where timestamp_start = \'{rBooking['timestamp_start']}\'"
        booking_q = booking.Booking()
        values = booking_q.query(rBooking)

        query = c.concatenate([query_s, values, query_e])
        print("update query:\n\n")
        print(query)


        try:
            # cursor.execute("update Prenotazione set id_causaleprenotazione = ? where timestamp_start = ?",
            #                (rBooking['id_causaleprenotazione'], rBooking['timestamp_start']))

            if To_Lockers_MSGs.cancelReservMQTTMsg(prenot):
                cursor.execute("update Prenotazione set id_causaleprenotazione = ? where timestamp_start = ?",
                               (rBooking['id_causaleprenotazione'], rBooking['timestamp_start']))
                # cursor.execute("update Prenotazione set id_causaleprenotazione = ? where  timestamp_start = ?",
                #                (status_temp, timestamp_start_temp))
                RES.setResult(0)
                RES.setMessage('Prenotazione aggiornata con successo.')

            else:
                RES.setResult(0)
                RES.setMessage('Prenotazione NON aggiornata con successo.')

            cursor.commit()
            cursor.close()
            connection['connection'].close()


        except pyodbc.Error as err:
            RES.dbError()
            RES.setResult(-1)
            RES.setErrors(str(err))

        return Response(RES.json(), status=status.HTTP_200_OK)

    ######## OLD VERSION TO UPDATE RESERVATION'S STATUS
    # def put(self, request):
    #     # per aggiornare le informazioni di una prenotazione
    #     RES.clean()
    #     serializer = self.serializer_class(request.user)
    #     user = serializer.data
    #     rBooking = request.data
    #
    #     #permissions
    #     if user["account_type"] != 'OPERATOR': # solo per amministratori?
    #         RES.permissionDenied()
    #         return Response(RES.json(), status=status.HTTP_200_OK)
    #
    #     #database connection
    #     connection = db.connectDB()
    #     if connection['esito'] == -1:
    #         RES.dbError()
    #         RES.setErrors(connection['connection'])
    #         return Response(RES.json(), status=status.HTTP_200_OK)
    #     cursor = connection['connection'].cursor()
    #
    #     #we check if the locker exists in our database
    #     query = f"select p.id_locker, p.waybill, p.ticket, p.id_causaleprenotazione, c.id_torre, c.id_box from Prenotazione p, Cassetto c where timestamp_start = \'{rBooking['timestamp_start']}\' and p.id_cassetto = c.id"
    #     cursor.execute(query)
    #     res = cursor.fetchone()
    #     if not res:
    #         RES.setMessage("La prenotazione che si vuole modificare non esiste.")
    #         return Response(RES.json(), status=status.HTTP_200_OK)
    #     else:
    #         cols = [cols[0] for cols in cursor.description]
    #         BOO = (dict(zip(cols, res)))
    #
    #     prenot = BOO.copy()
    #
    #     # Author: @josephineesposito - 27042025
    #     # AGGIUNTA STRUTTURA MESSAGGIO MQTT
    #
    #     mqtt_data = {
    #         'producer': 'BE',
    #         'message': 'Setta_Prenotazione',
    #             'data': {
    #                 'idTower': prenot['id_torre'],
    #                 'myBox': {
    #                     'id': prenot['id_box'],
    #                     'letteraVettura': prenot['waybill'],
    #                     'ticket': prenot['ticket'],
    #                     'id_causaleprenotazione': prenot['id_causaleprenotazione']
    #                 }
    #             }
    #     }
    #
    #     print(mqtt_data)
    #
    #     mqtt_msg = MQTT_MSG(
    #         topic=Topics.ToLocker.uniqueLocker + str(BOO['id_locker']),
    #         payload=mqtt_data
    #     )
    #
    #     mqtt_obj.connect()
    #
    #     if mqtt_obj.connected:
    #         mqtt_obj.publish_msg(mqtt_msg)
    #
    #     if not mqtt_obj.connected or not mqtt_obj.published:
    #         if not mqtt_obj.connected:
    #             logger.warning("MQTT NOT CONNECTED")
    #         if not mqtt_obj.published:
    #             logger.warning("MQTT MSG NOT PUBLISHED")
    #
    #         try:
    #             cursor.execute(
    #                 '''UPDATE Prenotazione SET id_causaleprenotazione = 'FAILED' and timestamp_end = ? WHERE timestamp_start = ?''',
    #                 c.get_date(), rBooking['timestamp_start'])
    #             cursor.commit()
    #         except pyodbc.Error as err:
    #             RES.dbError()
    #             RES.setErrors(str(err))
    #
    #     query_s = 'update Prenotazione set '
    #     query_e = f" where timestamp_start = \'{rBooking['timestamp_start']}\'"
    #     booking_q = booking.Booking()
    #     values = booking_q.query(rBooking)
    #
    #     query = c.concatenate([query_s, values, query_e])
    #     print("update query:\n\n")
    #     print(query)
    #
    #     try:
    #         cursor.execute(query)
    #         cursor.commit()
    #         cursor.close()
    #         connection['connection'].close()
    #         RES.setMessage('Prenotazione aggiornata con successo.')
    #     except pyodbc.Error as err:
    #         RES.dbError()
    #         RES.setErrors(str(err))
    #
    #     return Response(RES.json(), status=status.HTTP_200_OK)

    def post(self, request):
        # per aggiungere nuove prenotazioni
        RES.clean()
        serializer = self.serializer_class(request.user)
        user = serializer.data
        rBooking = request.data

        # permissions -> tutti i profili possono creare una prenotazione
        """
        if user['account_type'] < 1: #amministratore only?
            RES.permissionDenied()
            return Response(RES.json(), status=status.HTTP_200_OK)
        """

        # database connection
        connection = db.connectDB()
        if connection['esito'] == -1:
            RES.dbError()
            RES.setErrors(connection['connection'])
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()

        # variables
        db_booking = booking.Booking()
        db_booking = db_booking.base()

        timestamp = c.get_date()

        # query
        cursor.execute(f"select * from Prenotazione where timestamp_start = \'{timestamp}\'")
        res = cursor.fetchone()
        if res:
            RES.setMessage('Esiste già una prenotazione con questo timestamp_start.')
            RES.setResult(-1)
            return Response(RES.json(), status=status.HTTP_200_OK)

        # we convert and check the values to the correct ones!
        boo = booking.Booking(rBooking)
        boo = boo.validate()

        # variables
        boo['timestamp_start'] = c.get_date()

        # we get the tower number
        try:
            cursor.execute(f"select number from Torre where id = {boo['id_torre']}")
            res = cursor.fetchone()

            id_torre = res[0] if res else None


            cursor.execute(f"select id_box from Cassetto where id = {boo['id_cassetto']}")
            res = cursor.fetchone()
            id_box = res[0] if res else None


            if res:
                cols = [cols[0] for cols in cursor.description]
                print(dict(zip(cols, res)))


        except pyodbc.Error as err:
            RES.dbError()
            RES.setResult(-1)
            RES.setErrors(str(err))


        # we insert the data into the database
        try:
            cursor.execute('''insert into Prenotazione (timestamp_start, id_locker, id_torre, id_cassetto, timestamp_end, waybill, ticket, id_utente, id_causaleprenotazione)
                                     values(?, ?, ?, ?, ?, ?, ?, ?, ?)''', boo['timestamp_start'], boo['id_locker'],
                           boo['id_torre'], boo['id_cassetto'], boo['timestamp_end'], boo['waybill'], boo['ticket'],
                           user['id'], boo['id_causaleprenotazione'])

            cursor.commit()

            RES.setResult(0)
            RES.setMessage('Prenotazione inserita.')

            # BATOUL
            # MICHELE 270425
            # MODIFICATA STRUTTURA MESSAGGIO MQTT

            # BATOUL.. Move the MQTT MSG Format to mqttMsg Class and manage only DB Operations in this class
            if not To_Lockers_MSGs.addReservMQTTMsg(boo, id_torre, id_box):

            timestamp_message = c.get_date()

            mqtt_data = {
                "Producer": "Sparecube_Website",
                "Message": "reserve_box",
                "DateTime": timestamp_message,
                "Message_Id": "Sparecube_Website:reserve_box:" + timestamp_message,
                "Data": {
                    "idTower": rBooking['id_torre'],
                    "myBox": {
                        "id": rBooking['id_box'],
                        "letteraVettura": boo['waybill'],
                        "ticket": boo['ticket'],
                        "statoPrenotazione": boo['id_causaleprenotazione']
                    }
                }
            }


            print(mqtt_data)

            mqtt_msg = MQTT_MSG(
                topic=Topics.ToLocker.uniqueLocker + str(boo['id_locker']),
                payload=mqtt_data
            )

            mqtt_obj.connect()

            if mqtt_obj.connected:
                mqtt_obj.publish_msg(mqtt_msg)

            if not mqtt_obj.connected or not mqtt_obj.published:
                if not mqtt_obj.connected:
                    logger.warning("MQTT NOT CONNECTED")
                if not mqtt_obj.published:
                    logger.warning("MQTT MSG NOT PUBLISHED")


                try:
                    cursor.execute(
                        '''UPDATE Prenotazione SET id_causaleprenotazione = 'FAILED' WHERE id_locker = ? and id_torre = ? and id_cassetto = ? and timestamp_end = ?''',
                        boo['id_locker'], boo['id_torre'], boo['id_cassetto'], c.get_date())
                    cursor.commit()
                # Logger.info(Null, "Exception during publish to")
                except pyodbc.Error:
                    RES.dbError()



            cursor.close()
            connection['connection'].close()


        except pyodbc.Error as err:
            RES.dbError()
            RES.setResult(-1)
            RES.setErrors(str(err))

        return Response(RES.json(), status=status.HTTP_200_OK)


    ########## OLD VERSION TO POST NEW RESERVATION
    # def post(self, request):
    #     # per aggiungere nuove prenotazioni
    #     RES.clean()
    #     serializer = self.serializer_class(request.user)
    #     user = serializer.data
    #     rBooking = request.data
    #
    #     # permissions -> tutti i profili possono creare una prenotazione
    #     """
    #     if user['account_type'] < 1: #amministratore only?
    #         RES.permissionDenied()
    #         return Response(RES.json(), status=status.HTTP_200_OK)
    #     """
    #
    #     # database connection
    #     connection = db.connectDB()
    #     if connection['esito'] == -1:
    #         RES.dbError()
    #         RES.setErrors(connection['connection'])
    #         return Response(RES.json(), status=status.HTTP_200_OK)
    #     cursor = connection['connection'].cursor()
    #
    #     # variables
    #     db_booking = booking.Booking()
    #     db_booking = db_booking.base()
    #
    #     timestamp = c.get_date()
    #
    #     # query
    #     cursor.execute(f"select * from Prenotazione where timestamp_start = \'{timestamp}\'")
    #     res = cursor.fetchone()
    #     if res:
    #         RES.setMessage('Esiste già una prenotazione con questo timestamp_start.')
    #         RES.setResult(-1)
    #         return Response(RES.json(), status=status.HTTP_200_OK)
    #
    #     # we convert and check the values to the correct ones!
    #     boo = booking.Booking(rBooking)
    #     boo = boo.validate()
    #
    #     # variables
    #     boo['timestamp_start'] = c.get_date()
    #
    #     # we get the tower number
    #     try:
    #         cursor.execute(f"select number from Torre where id = {boo['id_torre']}")
    #         res = cursor.fetchone()
    #
    #         if res:
    #             cols = [cols[0] for cols in cursor.description]
    #             print(dict(zip(cols, res)))
    #
    #     except pyodbc.Error as err:
    #         RES.dbError()
    #         RES.setResult(-1)
    #         RES.setErrors(str(err))
    #
    #
    #     # we insert the data into the database
    #     try:
    #         cursor.execute('''insert into Prenotazione (timestamp_start, id_locker, id_torre, id_cassetto, timestamp_end, waybill, ticket, id_utente, id_causaleprenotazione)
    #                               values(?, ?, ?, ?, ?, ?, ?, ?, ?)''', boo['timestamp_start'], boo['id_locker'],
    #                        boo['id_torre'], boo['id_cassetto'], boo['timestamp_end'], boo['waybill'], boo['ticket'],
    #                        user['id'], boo['id_causaleprenotazione'])
    #
    #         cursor.commit()
    #
    #         RES.setResult(0)
    #         RES.setMessage('Prenotazione inserita.')
    #
    #         # BATOUL
    #         # MICHELE 270425
    #         # MODIFICATA STRUTTURA MESSAGGIO MQTT
    #
    #         mqtt_data = {
    #             'producer': 'BE',
    #             'message': 'Setta_Prenotazione',
    #                 'data': {
    #                     'idTower': rBooking['id_torre'],
    #                     'myBox': {
    #                         'id': rBooking['id_box'],
    #                         'letteraVettura': boo['waybill'],
    #                         'ticket': boo['ticket'],
    #                         'id_causaleprenotazione': boo['id_causaleprenotazione']
    #                     }
    #                 }
    #         }
    #
    #         print(mqtt_data)
    #
    #         mqtt_msg = MQTT_MSG(
    #             topic=Topics.ToLocker.uniqueLocker + str(boo['id_locker']),
    #             payload=mqtt_data
    #         )
    #
    #         mqtt_obj.connect()
    #
    #         if mqtt_obj.connected:
    #             mqtt_obj.publish_msg(mqtt_msg)
    #
    #         if not mqtt_obj.connected or not mqtt_obj.published:
    #             if not mqtt_obj.connected:
    #                 logger.warning("MQTT NOT CONNECTED")
    #             if not mqtt_obj.published:
    #                 logger.warning("MQTT MSG NOT PUBLISHED")
    #
    #             try:
    #                 cursor.execute(
    #                     '''UPDATE Prenotazione SET id_causaleprenotazione = 'FAILED' WHERE id_locker = ? and id_torre = ? and id_cassetto = ? and timestamp_end = ?''',
    #                     boo['id_locker'], boo['id_torre'], boo['id_cassetto'], c.get_date())
    #                 cursor.commit()
    #             # Logger.info(Null, "Exception during publish to")
    #             except pyodbc.Error:
    #                 RES.dbError()
    #
    #         cursor.close()
    #         connection['connection'].close()
    #
    #
    #     except pyodbc.Error as err:
    #         RES.dbError()
    #         RES.setResult(-1)
    #         RES.setErrors(str(err))
    #
    #     return Response(RES.json(), status=status.HTTP_200_OK)

    
    def delete(self,request, id):
        # per eliminare una prenotazione
        RES.clean()
        serializer = self.serializer_class(request.user)
        user = serializer.data

        #permissions
        if user["account_type"] != 'ADMIN': # solo per amministratori
            RES.permissionDenied()
            return Response(RES.json(), status=status.HTTP_200_OK)
        
        #database connection
        connection = db.connectDB()
        if connection['esito'] == -1:
            RES.dbError()
            RES.setErrors(connection['connection'])
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()
        
        #query
        try:
            cursor.execute(f"delete Prenotazione where timestamp_start = {id}")
            cursor.commit()
            cursor.close()
            connection['connection'].close()
            RES.setMessage('Prenotazione eliminata con successo.')

        except pyodbc.Error as err:
            RES.dbError()
            RES.setResult(-1)
            RES.setErrors(str(err))
        
        return Response(RES.json(), status=status.HTTP_200_OK)


"""
Class to get all Bookings data
GET     - get all data
"""
class BookingsAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get(self, request):
        # ritorna tutte le informazioni di tutti le prenotazioni
        RES.clean()
        serializer = self.serializer_class(request.user)
        user = serializer.data

        #permissions
        if user['account_type'] == 'USER': #solo per amministratori e utenti
            RES.permissionDenied()
            return Response(RES.json(), status=status.HTTP_200_OK)

        #database connection
        connection = db.connectDB()
        if connection['esito'] == -1:
            RES.dbError()
            RES.setErrors(str(connection['connection']))
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()

        #query
        bookings = []
        try:
            if user['account_type'] == 'OPERATOR':
                cursor.execute("""select P.timestamp_start, P.timestamp_end, P.id_causaleprenotazione, P.waybill, P.ticket, P.id_locker, T.number as id_torre, C.id_box as id_cassetto
                                    from Prenotazione as P, Torre as T, Cassetto as C
                                    where P.id_cassetto = C.id
                                    and P.id_torre = T.id
                                    and id_utente = ?""", (user['id'], ))
            else:
                cursor.execute("select * from Prenotazione")
            res = cursor.fetchall()

            if res:
                cols = [cols[0] for cols in cursor.description]
                for row in res:
                    BOO = booking.Booking(dict(zip(cols, row)))
                    bookings.append(BOO.json())
            cursor.close()
            connection['connection'].close()

            RES.setData(bookings)
        
        except pyodbc.Error as err:
            RES.dbError()
            RES.setErrors(str(err))

        return Response(RES.json(), status=status.HTTP_200_OK)


"""
Class to update Booking status
PUT    - update single booking status
"""
class BookStatusAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def put(self, request):
        # per aggiornare lo stato di una prenotazione
        RES.clean()
        serializer = self.serializer_class(request.user)
        user = serializer.data
        rBooking = request.data


        #permissions
        if user["account_type"] == 'USER': # solo per amministratori e operatori
            RES.permissionDenied()
            return Response(RES.json(), status=status.HTTP_200_OK)
        
        #database connection
        connection = db.connectDB()
        if connection['esito'] == -1:
            RES.dbError()
            RES.setErrors(connection['connection'])
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()

        #we check if the locker exists in our database
        cursor.execute('select * from Prenotazione where timestamp_start = ?', (rBooking['timestamp_start'], ))
        res = cursor.fetchone()
        if not res:
            RES.setMessage("La prenotazione che si vuole modificare non esiste.")
            return Response(RES.json(), status=status.HTTP_200_OK)

        try:
            cursor.execute("update Prenotazione set id_causaleprenotazione = ? where timestamp_start = ?", (rBooking['id_causaleprenotazione'], rBooking['timestamp_start']))
            cursor.commit()
            cursor.close()
            connection['connection'].close()
            RES.setResult(0)
            RES.setMessage('Prenotazione aggiornata con successo.')
        except pyodbc.Error as err:
            RES.dbError()
            RES.setResult(-1)
            RES.setErrors(str(err))

        return Response(RES.json(), status=status.HTTP_200_OK)


#endregion
# ====================.====================.====================.====================.==================== #


# ====================.====================.====================.====================.==================== #
#region | Logs
"""
Class to manage Database Logs
POST    - add new log info
"""
class LogAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def post(self, request):
        # per aggiungere nuovi log
        RES.clean()
        serializer = self.serializer_class(request.user)
        user = serializer.data
        rLog = request.data

        #permissions -> tutti possono inserire un log nel database
        """
        if user['account_type'] < 1: #amministratore only?
            RES.permissionDenied()
            return Response(RES.json(), status=status.HTTP_200_OK)
        """
        
        #database connection
        connection = db.connectDB()
        if connection['esito'] == -1:
            RES.dbError()
            RES.setErrors(connection['connection'])
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()

        #variables
        db_log = log.Log()
        db_log = db_log.base()

        #verifying data
        if set(rLog.keys()) != set(db_log.keys()):
            if all (key in rLog for key in ('id_utente', 'id_locker', 'id_prenotazione')):
                rLog['id_utente'] = user['id']
        
        #we convert and check the values to the correct ones!
        log_ = log.Log(rLog)
        log_ = log_.validate()
        log_['timestamp'] = c.get_date()
        
        try:
            cursor.execute('''insert into Log (timestamp, event, id_prenotazione, id_utente, id_locker) 
                              values( ?, ?, ?, ?, ?)''', log_['timestamp'], log_['event'], log_['id_prenotazione'], log_['id_utente'], log_['id_locker'])
            
            cursor.commit()
            cursor.close()
            connection['connection'].close()
            RES.setResult(0)
            RES.setMessage('Log inserito.')
        
        except pyodbc.Error as err:
            RES.dbError()
            RES.setResult(-1)
            RES.setData(rLog)
            RES.setErrors(str(err))
        
        return Response(RES.json(), status=status.HTTP_200_OK)
    
#endregion
# ====================.====================.====================.====================.==================== #


# ====================.====================.====================.====================.==================== #
#region | Joined views

"""
Class to manage Booking and Location joined view
GET     - get all data joined with Bookings and Locations (+ Lockers)
"""
class BookLocAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get(self, request):
        # ritorna tutte le informazioni di tutti le prenotazioni
        RES.clean()
        serializer = self.serializer_class(request.user)
        user = serializer.data

        #permissions
        if user['account_type'] != 'ADMIN' and user['account_type'] != 'OPERATOR': #solo per amministratori e operatori
            RES.permissionDenied()
            return Response(RES.json(), status=status.HTTP_200_OK)

        #database connection
        connection = db.connectDB()
        if connection['esito'] == -1:
            RES.dbError()
            RES.setErrors(str(connection['connection']))
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()

        #query
        query = []
        try:
            cursor.execute("""
                            select timestamp_start, timestamp_end, waybill, ticket, id_utente, id_locker, id_cassetto, city, road, id_causaleprenotazione
                            from Prenotazione as p, Localita as lc, Locker as lk
                            where p.id_locker = lk.id
                            and lk.localita = lc.id
                            """)
            res = cursor.fetchall()

            if res:
                # Costruzione dei dati da restituire
                cols = [col[0] for col in cursor.description]
                
                for row in res:
                    booking_data = dict(zip(cols, row))
                    query.append(booking_data)

            cursor.close()
            connection['connection'].close()

            RES.setData(query)
        
        except pyodbc.Error as err:
            RES.dbError()
            RES.setErrors(str(err))

        return Response(RES.json(), status=status.HTTP_200_OK)


"""
Class to manage Towers and Drawers joined view
GET    - get all data joined with Towers and Drawers
"""
class TowersDrawersAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get(self, request):
        # ritorna tutte le informazioni di tutti i cassetti
        RES.clean()
        serializer = self.serializer_class(request.user)
        user = serializer.data

        #permissions
        if user['account_type'] != 'ADMIN' and user['account_type'] != 'OPERATOR': #solo per amministratori e operatori
            RES.permissionDenied()
            return Response(RES.json(), status=status.HTTP_200_OK)

        #database connection
        connection = db.connectDB()
        if connection['esito'] == -1:
            RES.dbError()
            RES.setErrors(str(connection['connection']))
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()

        #query
        try:
            lockers = []
            cursor.execute("""
                            select t.id_locker, c.id_torre, c.id_box, c.width, c.height, c.depth, c.status, c.is_full, c.is_open
                            from Torre as t
                            join Cassetto c on c.id_torre = t.id
                            join Locker l on t.id_locker = l.id
                            left join Prenotazione P on p.id_cassetto = c.id
                            where p.id_causaleprenotazione is null or p.id_causaleprenotazione != 'OPEN'
                            """)
            res = cursor.fetchall()

            if res:
                cols = [col[0] for col in cursor.description]
                
                for row in res:
                    locker_data = dict(zip(cols, row))
                    lockers.append(locker_data)

            cursor.close()
            connection['connection'].close()

            RES.setData(lockers)
        
        except pyodbc.Error as err:
            RES.dbError()
            RES.setErrors(str(err))

        return Response(RES.json(), status=status.HTTP_200_OK)

#endregion
# ====================.====================.====================.====================.==================== #

