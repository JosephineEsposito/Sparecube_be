# region | IMPORTS
# for env vars
import os

#from rest framework
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import UserSerializer, SignInSerializer, ChangePassword

# for DB
import pyodbc

# - for time
from utils import crypt as c
# for Response Format
from utils import output as r
# for Database connection
from utils import database as db
# for Email
from utils import email as e
# for User
from utils.data import user as u

#::--->> Aggiunto per custom login
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from django.http import JsonResponse
from django.contrib.auth import authenticate, update_session_auth_hash
from django.conf import settings
# Temporary 
import logging
import json
logger = logging.getLogger('capri')
#endregion


# ====================.====================.====================.====================.==================== #
#region | Custom functions and global variables
# ====================. GLOBAL VARIABLES .==================== #
RES = r.Output()
TYP = ""


# ====================. GLOBAL FUNCTIONS .==================== #
def fillType(cursor):
    cursor.execute("SELECT descrizione FROM DB_CAPRI.dbo.AccountType")
    result = cursor.fetchall()

    if result:
        res = {
            "user" : result[0],
            "driv" : result[1],
            "oper" : result[2],
            "admi" : result[3]
        }
        TYP = r.Type(res)
        
        
#endregion
# ====================.====================.====================.====================.==================== #




# ====================.====================.====================.====================.==================== #
# region | ACCOUNT

"""
Class to manage the account
GET     - single (self) user info
PUT     - update single user info
DELETE  - delete (self) user info
"""
class UserAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer
    
    def get(self, request):
        # ritorna tutte le informazioni di tutti gli utenti
        RES.clean()
        
        # Query
        try:
            serializer = self.serializer_class(request.user)
            user = u.User(serializer.data)
            
            RES.setData(user.json())

            return Response(RES.json(), status=status.HTTP_200_OK)
            
        except:
            RES.dbError()
        
        return Response(RES.json(), status=status.HTTP_200_OK)

    def put(self, request):
        # per aggiornare le informazioni di un utente (self only)
        serializer_data = request.data.get('user', {})
        serializer = UserSerializer(request.user, data=serializer_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        RES.clean()
        RES.setData(serializer.data)
        
        return Response(RES.json(), status=status.HTTP_200_OK)

    def delete(self, request):
        # deletes the user that makes the request
        RES.clean()
        user = self.request.user
        user.delete()

        RES.setMessage("Account eliminato con successo.")
        return Response(RES.json(), status=status.HTTP_200_OK)


"""
Class to update externally a user
PUT     - update single user info by id
"""
class UpdateUserAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def put(self, request, id):
        # per aggiornare i dati di un utente dall'esterno
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
            RES.setErrors(connection['connection'])
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()

        #query
        try:
            cursor.execute('update account_utente set is_active = 0 where id = ?', id)
            cursor.commit()
            cursor.close()
            connection['connection'].close()
            RES.setMessage('Account disattivato con successo.')
            RES.setResult(0)

        except pyodbc.Error as err:
            RES.dbError()
            RES.setErrors(str(err))

        return Response(RES.json(), status=status.HTTP_200_OK)


"""
Class to get all users data
GET     - get all users data
"""
class UsersAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get(self, request):
        # ritorna una lista di tutti gli utenti
        RES.clean()
        serializer = self.serializer_class(request.user)
        user = serializer.data

        # permissions (solo per amministratori)
        if user["account_type"] != 'ADMIN':
            RES.permissionDenied()
            return Response(RES.json(), status=status.HTTP_200_OK)
        
        # Connessione al database
        connection = db.connectDB()
        if connection['esito'] == -1:
            RES.dbError()
            RES.setErrors(str(connection['connection']))
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()

        # query
        try:
            accounts = []
            cursor.execute("SELECT id, id_azienda, first_name, last_name, username, email, account_type, is_active, is_staff, is_superuser FROM account_utente")
            res = cursor.fetchall()
            if res:
                cols = [col[0] for col in cursor.description]
                for row in res:
                    accounts.append(u.User(dict(zip(cols, row))).json())
            
            cursor.close()
            connection['connection'].close()
            RES.setData(accounts)
        
        except pyodbc.Error as err:
            RES.dbError()
            RES.setErrors(str(err))
        
        return Response(RES.json(), status=status.HTTP_200_OK)

"""
Class to manage signup for accounts
POST    - create user account (for all)
"""
class CreateUserAPIView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        # per creare un nuovo account di qualsiasi tipo per adesso
        RES.clean()
        user = request.data # i dati del nuovo account

        #database connection
        connection = db.connectDB()
        if connection['esito'] == -1:
            RES.dbError()
            RES.setErrors(str(connection['connection']))
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()

        #query
        try:
            cursor.execute("select id from account_utente where email = ?", user['email'])
            res = cursor.fetchone()

            if res:
                RES.setMessage("L\'email proporzionata è già presente nel nostro sistema.")
                return Response(RES.json(), status=status.HTTP_200_OK)
            cursor.close()
            connection['connection'].close()

            serializer = UserSerializer(data=user)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            #email
            """
            em = e.send(os.environ['PROJECT'], 'Confermiamo che la registrazione è andata a buon fine. Enjoy ;)', user['email'], None)
            if em['status'] == -1:
                RES.setErrors(em['message'])
                RES.setMessage('L\'email è già prensente nel sistema.')
            """
            
            RES.setMessage("La registrazione è andata a buon fine. A breve riceverai un\'email da confermare.")
            RES.setResult(0)

        except pyodbc.Error as err:
            RES.dbError()
            RES.setErrors(str(err))

        return Response(RES.json(), status=status.HTTP_200_OK)


"""
Class to manage login for accounts
POST    - login user account (for all)
"""
class LoginUserAPIView(APIView):
    permission_classes = ()
    authentication_classes = ()

    def post(self, request):
        # login per tutti i tipi di account
        received_json_data = request.data
        serializer = SignInSerializer(data=received_json_data)
        logger.debug('received data')

        if serializer.is_valid():
            logger.debug('data is valid')
            logger.debug(json.dumps(settings.DATABASES))

            user = authenticate(
                request,
                username=received_json_data['email'],
                password=received_json_data['password'])
            
            if user is not None:
                logger.debug('user found')
                refresh = RefreshToken.for_user(user)
                logger.debug('token found')
                return JsonResponse({'refresh_token' : str(refresh), 'access_token' : str(refresh.access_token),}, status=200)
            else:
                logger.debug('user not found')
                return JsonResponse({'message': 'Le credenziali non sono valide'}, status=401)
        else:
            return JsonResponse({'message': serializer.errors}, status=400)


"""
Class to manage password recovery for accounts
POST    - API to change password
PATCH   - Create a personalized url to change password
"""
class PasswordAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    user_serializer_class = UserSerializer
    pasw_serializer_class = ChangePassword

    def post(self, request):
        RES.clean()
        
        user = request.user
        old_password = request.data['old_password']
        new_password = request.data['new_password']

        if user.check_password(old_password):
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)
            return Response(RES.json(), status=status.HTTP_200_OK)
        RES.setMessage("La password inserita non è corretta.")
        return Response(RES.json(), status=status.HTTP_200_OK)
    
    def patch(self, request):
        RES.clean()
        email = request.data['email']
        serializer = self.user_serializer_class(request.user)
        user = serializer.data

        access_token = request.META.get('HTTP_AUTHORIZATION', "")
        token = access_token[7:]

        url = f"{os.environ['FRONTEND']}/reset/{user['id']}/{c.get_time(timelim=1000)}/{token}"

        txt = "Di recente hai richiesto di reimpostare la password del tuo account dell'app Sparecube. Dai click al link di sotto per completare l'azione. Questo link è valido solo per i prossimi 30 minuti."
        em = e.send('Sparecube: password', txt, email, user['username'], link=url)
        if em['status'] == -1:
            RES.setErrors(em['message'])
            RES.setMessage('L\'email non è presente nel nostro sistema.')
            return Response(RES.json(), status=status.HTTP_200_OK)
        
        RES.setMessage('A breve riceverai un\'email per il ripristino della password.')
        return Response(RES.json(), status=status.HTTP_200_OK)
    
    def options(self, request):
        RES.clean()
        RES.setMessage('Success!')
        return Response(RES.json(), status=status.HTTP_200_OK)
        

# endregion
# ====================.====================.====================.====================.==================== #
