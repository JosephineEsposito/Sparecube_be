"""
Manager of the database connections
"""

# for env vars
import os

import pyodbc



def connectDB():
    print("...Connecting to the Database")
    connectionString = "Driver={ODBC Driver 17 for SQL Server};Server="+os.environ["DB_ADDRESS"]+";Database="+os.environ["DB_NAME"]+";Trusted_Connection=No;UID="+os.environ["DB_USER"]+";PWD="+ os.environ["DB_PASSWORD"] +";"

    try:
        connection = pyodbc.connect(connectionString)
        esito = 0
        print("Connection established!")
        #fillType(connection.cursor())
    except pyodbc.Error as pe:
        print("[-1]: ", pe)
        esito = -1
        connection = pe

    result = {
        "esito" : esito,
        "connection" : connection
    }
    return result
