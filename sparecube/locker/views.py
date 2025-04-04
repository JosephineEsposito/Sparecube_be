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
# for Cassetto
from utils.data import drawer
# for Prenotazione
from utils.data import booking
# for Logs
from utils.data import log

#endregion



# ====================.====================.====================.====================.==================== #
#region | Custom functions and global variables
# ====================. GLOBAL VARIABLES .==================== #

RES = o.Output() # Formato per ritornare i dati

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
        cursor.execute(f'select * from Localita where id = {rLocalita['id']}')
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
            cursor.execute(f'delete Localita where id = {id}')
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
            locations = []
            cursor.execute("select * from Localita")
            res = cursor.fetchall()

            if res:
                cols = [cols[0] for cols in cursor.description]
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
GET     - all locker infos
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
            cursor.close()
            connection['connection'].close()

            RES.setData(LOC.json())

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
        cursor.execute(f'select * from Locker where id = {rLocker['id']}')
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
        cursor.execute(f'select * from Locker where number = {rLocker['number']}')
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
            cursor.execute(f'delete Cassetto where id_locker = {id}')
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
            cursor.execute(f'delete Locker where id = {id}')
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
            lockers = []
            cursor.execute("select * from Locker")
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
#region | Cassetto
"""
Class to manage Cassetto
GET     - single (id) drawer info
GET     - all drawer infos
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
        cursor.execute(f'select * from Cassetto where id = {rDrawer['id']}')
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
            cursor.execute(f'delete Cassetto where id = {id}')
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
        if user['account_type'] != 'ADMIN': #solo per amministratori
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


#endregion
# ====================.====================.====================.====================.==================== #


# ====================.====================.====================.====================.==================== #
#region | Prenotazioni
"""
Class to manage Prenotazioni
GET     - single (id) booking info
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
        cursor.execute(f'select * from Prenotazione where timestamp_start = {rBooking['timestamp_start']}')
        res = cursor.fetchone()
        if not res:
            RES.setMessage("La prenotazione che si vuole modificare non esiste.")
            return Response(RES.json(), status=status.HTTP_200_OK)
        
        query_s = 'update Prenotazione set '
        query_e = f" where timestamp_start = {rBooking['timestamp_start']}"
        booking_q = booking.Booking()
        values = booking_q.query(rBooking)

        query = c.concatenate([query_s, values, query_e])

        try:
            cursor.execute(query)
            cursor.commit()
            cursor.close()
            connection['connection'].close()
            RES.setMessage('Prenotazione aggiornata con successo.')
        except pyodbc.Error as err:
            RES.dbError()
            RES.setErrors(str(err))

        return Response(RES.json(), status=status.HTTP_200_OK)

    def post(self, request):
        # per aggiungere nuove prenotazioni
        RES.clean()
        serializer = self.serializer_class(request.user)
        user = serializer.data
        rBooking = request.data

        #permissions -> tutti i profili possono creare una prenotazione
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
        db_booking = booking.Booking()
        db_booking = db_booking.base()

        timestamp = c.get_date()

        #query
        cursor.execute(f'select * from Prenotazione where timestamp_start = \'{timestamp}\'')
        res = cursor.fetchone()
        if res:
            RES.setMessage('Esiste già una prenotazione con questo timestamp_start.')
            RES.setResult(-1)
            return Response(RES.json(), status=status.HTTP_200_OK)
                
        #we convert and check the values to the correct ones!
        boo = booking.Booking(rBooking)
        boo = boo.validate()
        
        #variables
        boo['timestamp_start'] = c.get_date()

        #we insert the data into the database
        try:
            cursor.execute('''insert into Prenotazione (timestamp_start, id_locker, id_cassetto, timestamp_end, waybill, ticket, id_utente, id_causaleprenotazione)
                              values(?, ?, ?, ?, ?, ?, ?, ?)''', boo['timestamp_start'], boo['id_locker'], boo['id_cassetto'], boo['timestamp_end'], boo['waybill'], boo['ticket'], user['id'], boo['id_causaleprenotazione'])
            
            cursor.commit()
            cursor.close()
            connection['connection'].close()
            RES.setResult(0)
            RES.setMessage('Prenotazione inserita.')
        
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
            cursor.execute(f'delete Prenotazione where timestamp_start = {id}')
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
        if user['account_type'] != 'ADMIN': #solo per amministratori
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




#endregion
# ====================.====================.====================.====================.==================== #

