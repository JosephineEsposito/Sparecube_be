"""
Dropbox Manager
"""

# DROPBOX MANAGEMENT
import dropbox

import os
import base64
# PATH FOR DOCUMENTS
from pathlib import Path

# ====================.====================.====================.====================.==================== #
#region | Dropbox management
# Per convertire img a base64
def img():
    image_path = "D:/GitHub/Backend/Capri/backend/APIaccount/pate.jpg" #input("Image path: ")
    with open(image_path, 'rb') as image_file:
        image_bytes = image_file.read()
        base64_string = base64.b64encode(image_bytes).decode("utf-8")
        return base64_string

# riceve image in b64 + tipo e fa l'upload
def image_converter(image, u_id, tipo = 'jpg'):
    access = refresh()
    if access == -1:
        return -1
    dbx = dropbox.Dropbox(access)

    if image.startswith('data:'):
        _, image = image.split(',', 1)
    
    image_bytes = base64.b64decode(image)
    path = f'/APIDocumenti/{str(u_id)}.{tipo}'
    dbx.files_upload(image_bytes, path, mode=dropbox.files.WriteMode.overwrite)
    return 'Done'

def image_deconverter(u_id):
    tipo = 'jpg'
    #access to dropbox
    access = refresh()
    if access == -1:
        return -1
    dbx = dropbox.Dropbox(access)

    
    BASE_DIR = Path(__file__).resolve().parent.parent
    local_path = str(BASE_DIR) + "\\" + str(u_id) + '.' + tipo

    try:
        #we download the document
        dbx_path = f'/APIDocumenti/{str(u_id)}.jpg'
        dbx.files_download_to_file(local_path, dbx_path)
    except:
        try:
            #we download the document
            dbx_path = f'/APIDocumenti/{str(u_id)}.jpeg'
            dbx.files_download_to_file(local_path, dbx_path)
        except:
            return -1


    #we convert it to b64
    with open(local_path, 'rb') as image_file:
        image_bytes = image_file.read()
        base64_string = base64.b64encode(image_bytes).decode("utf-8")
    
    #we remove the file afterwards
    os.remove(local_path)
    
    #we return the b64 file
    return base64_string


#endregion
# ====================.====================.====================.====================.==================== #


def refresh():
    dbx = dropbox.Dropbox(
        oauth2_refresh_token= os.environ['DROPBOX_REFRESH_KEY'],
        app_key= os.environ['DROPBOX_APP_KEY'],
        app_secret= os.environ['DROPBOX_APP_SECRET']
    )

    # Refresh the access token
    try:
        dbx.refresh_access_token()
        new_access_token = dbx._oauth2_access_token
        #print("New Access Token:", new_access_token)
        return new_access_token
    except dropbox.exceptions.AuthError as e:
        print("Error refreshing access token:", e)
        return -1
