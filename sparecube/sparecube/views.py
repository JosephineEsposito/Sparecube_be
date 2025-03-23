# region | IMPORTS

#from rest framework
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

# for Response Format
from utils import output as r
# for Database connection
from utils import database as db

#::--->> Aggiunto per custom login
from rest_framework.views import APIView
# Temporary 
import logging
logger = logging.getLogger('capri')
#endregion


# ====================.====================.====================.====================.==================== #
#region | Custom functions and global variables
# ====================. GLOBAL VARIABLES .==================== #
RES = r.Output()

class HelloAPIView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        RES.clean()
        RES.setMessage("Pong! This is the backend!")
        return Response(RES.json(), status=status.HTTP_200_OK)
    
class DBTestApiView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        RES.clean()

        #database connection
        connection = db.connectDB()
        if connection['esito'] == -1:
            RES.dbError()
            RES.setErrors(str(connection['connection']))
            return Response(RES.json(), status=status.HTTP_200_OK)
        cursor = connection['connection'].cursor()
        
        cursor.close()
        connection['connection'].close()

        RES.setMessage("Database connection is successful!")

        return Response(RES.json(), status=status.HTTP_200_OK)



