#region | IMPORTS
from django.db.models.functions import Concat
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
from utils.data import user
# for Logs
from utils.data import log
# for MQTT
from locker.mqttMsg import To_Lockers_MSGs
from utils.MQTT import mqtt_obj, MQTT_MSG, Topics
import logging
# for mailersend
from utils import email

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
        if user["account_type"] == 'USER' or user["account_type"] == 'SUPERVISOR': # solo per amministratori e operatori (limitato)
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


"""
Class to get all Locations for map
"""
class LocationMapView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get(self, request):
        # ritorna tutti i dettagli di tutte le locations
        RES.clean()
        serializer = self.serializer_class(request.user)
        user = serializer.data

        #permissions
        if user["account_type"] != 'OPERATOR': # solo per operatori
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
                cursor.execute("select L.*, LO.id as id_locker from Localita as L left join Locker as LO on L.id = LO.localita")
                res = cursor.fetchall()

                if res:
                    cols = [col[0] for col in cursor.description]
                    for row in res:
                        LOC = location.Location(dict(zip(cols, row)))
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
        if user["account_type"] == 'USER' or user["account_type"] == 'SUPERVISOR' : # solo per amministratori e operatori (limitato)
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
                cursor.execute("select L.id, LO.city as city, LO.road as localita, L.id_azienda, L.status from Locker as L, Localita as LO where L.localita = LO.id")
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
        if user["account_type"] == 'USER' or user["account_type"] == 'SUPERVISOR': # solo per amministratori e operatori (limitato)
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
        if user['account_type'] == 'USER' or user['account_type'] == 'SUPERVISOR': #solo per amministratori e operatori (limitato)
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
        if user['account_type'] == 'USER' or user['account_type'] == 'SUPERVISOR': #solo per amministratori e operatori (limitato)
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

        #we check if the locker exists in our database
        query = f"select c.is_full, p.id_locker, p.waybill, p.ticket, p.id_causaleprenotazione, t.number as id_torre, c.id_box from Prenotazione p, Cassetto c, Torre t where timestamp_start like \'%{rBooking['timestamp_start']}%\' and p.id_cassetto = c.id and p.id_torre = t.id"
        cursor.execute(query)
        res = cursor.fetchone()

        if not res:
            RES.setMessage("La prenotazione che si vuole modificare non esiste.")
            return Response(RES.json(), status=status.HTTP_200_OK)
        else:
            cols = [cols[0] for cols in cursor.description]
            BOO = (dict(zip(cols, res)))


        # Author: @josephineesposito - 27042025
        # AGGIUNTA STRUTTURA MESSAGGIO MQTT
        # Batoul..
        # Move forming MQTT Msg to mqttMsg class
        # Make the reservation status updated to the new status if only the mqtt msg published successfully.

        prenot = BOO.copy()

        try:
            if prenot['is_full'] == True:
                RES.setResult(0)
                RES.setMessage('The Box is full ')
                print('The Box is full ')
                return Response(RES.json(), status=status.HTTP_200_OK)

            if To_Lockers_MSGs.cancelReservMQTTMsg(prenot):
                query = f"update Prenotazione set id_causaleprenotazione = \'{rBooking['id_causaleprenotazione']}\' where timestamp_start like \'%{rBooking['timestamp_start']}%\'"
                cursor.execute(query)
                
                RES.setResult(0)
                RES.setMessage('Prenotazione aggiornata con successo.')

            else:
                RES.setResult(0)
                RES.setMessage('Prenotazione NON aggiornata con successo.')

            print(RES.json())
            cursor.commit()
            cursor.close()
            connection['connection'].close()


        except pyodbc.Error as err:
            RES.dbError()
            RES.setResult(-1)
            RES.setErrors(str(err))

        print(RES.json())
        return Response(RES.json(), status=status.HTTP_200_OK)

    def post(self, request):
        # per aggiungere nuove prenotazioni
        RES.clean()
        serializer = self.serializer_class(request.user)
        user_data = serializer.data
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

        # region Get the supervisor user
        supervisor_id = rBooking.get("id_supervisor")
        print(f"id_supervisor: {supervisor_id}")
       # supervisor_data = None
        if supervisor_id:
            try:
                query = f"SELECT id, id_azienda, first_name, last_name, username, email, account_type, is_active, is_staff, is_superuser FROM account_utente WHERE id = ?"
                print (query)
                cursor.execute(query,supervisor_id)
                row = cursor.fetchone()
                if row:
                    cols = [column[0] for column in cursor.description]
                    supervisor_data = dict(zip(cols, row))
            except pyodbc.Error as err:
                RES.dbError()
                RES.setErrors(str(err))
                return Response(RES.json(), status=status.HTTP_200_OK)

        print("supervisor_ data", supervisor_data)

        supervisor_user = user.User(supervisor_data) # if supervisor_data else None
        print("supervisor", supervisor_user)
        # endregion



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

        cursor.execute("select * from Prenotazione")
        all_results = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]

        ticket = 0
        waybill = 0



        for row in all_results:
            row_dict = dict(zip(column_names, row))
            if boo['ticket'] == row_dict['ticket']:
                print(f"ticket not unique")
                ticket = ticket + 1
                # RES.setResult(0)
                # RES.setMessage('ticket not unique.')
                # return Response(RES.json(), status=status.HTTP_200_OK)

            if boo['waybill'] == row_dict['waybill']:
                print(f"waybill not unique")
                waybill = waybill + 1
                # RES.setResult(0)
                # RES.setMessage('waybill not unique.')
                # return Response(RES.json(), status=status.HTTP_200_OK)

        if ticket > 0 and waybill > 0:
            RES.setResult(0)
            RES.setMessage('ticket and waybill not unique.')
            return Response(RES.json(), status=status.HTTP_200_OK)

        if ticket > 0 and waybill == 0:
            RES.setResult(0)
            RES.setMessage('ticket and unique.')
            return Response(RES.json(), status=status.HTTP_200_OK)

        if waybill > 0 and ticket == 0:
            RES.setResult(0)
            RES.setMessage('waybill and unique.')
            return Response(RES.json(), status=status.HTTP_200_OK)

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
            cursor.execute('''insert into Prenotazione (timestamp_start, id_locker, id_torre, id_cassetto, timestamp_end, waybill, ticket, id_utente, id_causaleprenotazione, operation_type, id_supervisor)
                                     values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', boo['timestamp_start'], boo['id_locker'],
                           boo['id_torre'], boo['id_cassetto'], boo['timestamp_end'], boo['waybill'], boo['ticket'],
                           user_data['id'], boo['id_causaleprenotazione'], boo['operation_type'], supervisor_user.id)

            cursor.commit()
            RES.setResult(0)
            RES.setMessage('Prenotazione inserita.')

            cursor.execute('select loc.* from Locker l join Localita loc on l.localita = loc.id where l.id = ?', boo['id_locker'])
            row = cursor.fetchone()
            column_names = [desc[0] for desc in cursor.description]
            lockerLoc = dict(zip(column_names, row))

            address = lockerLoc['road']

            if lockerLoc['civicnumber'] > 0:
                address = f"{lockerLoc['road']}, {lockerLoc['civicnumber']}"

            userList = [user_data, supervisor_user]

            subject = f"Prenotazione (L.Vettura: {boo['waybill']} - Ticket: {boo['ticket']})"

            body = (
                f"L'utente {user_data['first_name'].capitalize()} {user_data['last_name'].capitalize()} ha inserito una nuova prenotazione:<br><br>"
                f"- Lettera di vettura: {boo['waybill']}<br>"
                f"- Ticket: {boo['ticket']}<br><br><br>"
                "Locker assegnato:<br><br>"
                f"Locker Nr.{boo['id_locker']}<br>"
                f"{address}<br>"
                f"{lockerLoc['postalcode']}<br>"
                f"{lockerLoc['city']} ({lockerLoc['provincia']})"
            )

            if not To_Lockers_MSGs.addReservMQTTMsg(boo, id_torre, id_box):
                try:
                    cursor.execute(
                        '''UPDATE Prenotazione SET id_causaleprenotazione = 'FAILED' WHERE id_locker = ? and id_torre = ? and id_cassetto = ?''',
                        boo['id_locker'], boo['id_torre'], boo['id_cassetto'])
                    cursor.commit()
                    RES.setMessage('Prenotazione fallita')

                    subject = "Prenotazione Fallita"
                    body = f"Prenotazione da parte dell'utente {user['username']} non riuscita"

                # Logger.info(Null, "Exception during publish to")
                except pyodbc.Error:
                    RES.dbError()

            cursor.close()
            connection['connection'].close()

            chimp = email.MailChimp()
            chimp.send(subject, body, userList)

        except pyodbc.Error as err:
            RES.dbError()
            RES.setResult(-1)
            RES.setErrors(str(err))

        return Response(RES.json(), status=status.HTTP_200_OK)
    
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
        if user['account_type'] == 'USER': #solo per amministratori e operatori
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
                cursor.execute("""
                    SELECT P.timestamp_start, P.timestamp_end, P.id_causaleprenotazione, P.waybill, P.ticket,
                        P.id_locker, T.number AS id_torre, C.id_box AS id_cassetto,
                        lc.city, lc.road, P.SDA_Code,
                        CONCAT(us.first_name, ' ', us.last_name) AS supervisor
                    FROM Prenotazione P
                    JOIN Cassetto C ON P.id_cassetto = C.id
                    JOIN Torre T ON P.id_torre = T.id
                    JOIN Locker lk ON T.id_locker = lk.id
                    JOIN Localita lc ON lk.localita = lc.id
                    LEFT JOIN account_utente us ON P.id_supervisor = us.id
                    WHERE P.id_utente = ?
                """, (user['id'],))

            elif user['account_type'] == 'SUPERVISOR':
                cursor.execute("""select P.timestamp_start, P.timestamp_end, P.id_causaleprenotazione, P.waybill, P.ticket, P.id_locker, T.number as id_torre, C.id_box as id_cassetto, lc.city, lc.road
                                                    from Prenotazione as P, Torre as T, Cassetto as C, Locker as lk, Localita as lc
                                                    where P.id_cassetto = C.id
                                                    and P.id_torre = T.id
                                                    and T.id_locker = lk.id
                                                    and lk.localita = lc.id
                                                    and id_supervisor = ?""", (user['id'],))
            else:
                cursor.execute("select * from Prenotazione")
            res = cursor.fetchall()

            if res:
                cols = [cols[0] for cols in cursor.description]
                for row in res:
                    BOO = booking.Booking(dict(zip(cols, row)))
                    BOO.clean_timestamp()
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
        if user["account_type"] == 'USER' or user["account_type"] == 'SUPERVISOR': # solo per amministratori e operatori
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
            # OLD_Query
            # cursor.execute("""
            #                 select p.timestamp_start, p.timestamp_end, p.waybill, p.ticket, p.id_utente, p.id_locker, c.id_box as id_cassetto, t.number as id_torre, lc.city, lc.road, p.id_causaleprenotazione, p.SDA_Code, p.id_supervisor
            #                 from Prenotazione as p, Localita as lc, Locker as lk, Torre as t, Cassetto as c, account_utente as u
            #                 where p.id_locker = lk.id
            #                 and lk.localita = lc.id
            #                 and p.id_torre = t.id
            #                 and p.id_cassetto = c.id
            #                 """)
            cursor.execute("""select p.timestamp_start, p.timestamp_end, p.waybill, p.ticket,  p.id_locker,
            t.number as id_torre, c.id_box as id_cassetto, loc.city, loc.road, p.id_causaleprenotazione, p.SDA_Code, au.id as id_utente,
            concat (au.first_name,' ',au.last_name) as operator_name, concat (us.first_name,' ',us.last_name) as supervisor
            from Prenotazione p
            join cassetto c on p.id_cassetto = c.id
            join torre t on c.id_torre = t.id
            join locker l on t.id_locker = l.id
            join Localita loc on l.localita = loc.id
            join account_utente au on p.id_utente = au.id
            join account_utente us on p.id_supervisor = us.id""")
            res = cursor.fetchall()

            if res:
                # Costruzione dei dati da restituire
                cols = [col[0] for col in cursor.description]
                
                for row in res:
                    booking_data = dict(zip(cols, row))
                    if booking_data['timestamp_start'] : booking_data['timestamp_start'] = booking_data['timestamp_start'].split('.')[0]
                    if booking_data['timestamp_end']   : booking_data['timestamp_end']   = booking_data['timestamp_end'].split('.')[0]
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

        query = ""
        if user['account_type'] == 'ADMIN':
            query = """
                            WITH UltimaPrenotazione AS (
                                SELECT *, 
                                    ROW_NUMBER() OVER (PARTITION BY id_cassetto ORDER BY timestamp_start DESC) as rn
                                FROM Prenotazione
                            )
                            SELECT 
                                t.id_locker, 
                                t.number AS id_torre, 
                                c.id_box, 
                                c.width, 
                                c.height, 
                                c.depth, 
                                c.status, 
                                c.is_full, 
                                c.is_open
                            FROM Torre t
                            JOIN Cassetto c ON c.id_torre = t.id
                            JOIN Locker l ON t.id_locker = l.id
                            LEFT JOIN UltimaPrenotazione p ON p.id_cassetto = c.id AND p.rn = 1
                            
                            """
        if user['account_type'] == 'OPERATOR':
            query = """
                            select t.id_locker, c.id_torre, c.id_box, c.width, c.height, c.depth, c.status, c.is_full, c.is_open
                            from Torre as t
                            join Cassetto c on c.id_torre = t.id
                            join Locker l on t.id_locker = l.id
                            left join Prenotazione P on p.id_cassetto = c.id
                            where p.id_causaleprenotazione is null or p.id_causaleprenotazione != 'OPEN'
                            """

        #query
        try:
            lockers = []
            cursor.execute(query)
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

