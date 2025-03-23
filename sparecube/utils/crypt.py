# Gestione della encrypt/decrypt in AES

# region | IMPORTS

# for env vars
import os

# for encryption
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes
import base64

# for random
from random import randint
import string
import random

# for time and timestamp
from datetime import datetime as dt

# endregion



# SECRET KEY FOR AES
key = os.environ['AES_SECRET_KEY']
secret_key = bytes.fromhex(key)
delim = '\n'

passphrase = os.environ['AES_PASSPHRASE']


# region | Time and String

# >> format string time
def format(string_time):
    new_time = string_time[0:10] + 'T' + string_time[11:]
    return new_time[0:-1]

# >> get current timestamp / or from date
def get_time(date = dt.now(), timelim = 100):
    return int(dt.timestamp(date) * timelim)

# >> to get current date
def get_date():
    #2022-09-20 10:27:21.240752
    return dt.now()

# >> to concatenate strings
def concatenate(str_):
    total_str = ''
    for i in range(len(str_)):
        total_str += str(str_[i])
    return total_str

# endregion


# region | Random

# >> to create a random ID
def randID(text, time_stamp):
    unique_id = ''
    unique_id = text + delim + string(int(time_stamp))
    return unique_id

# >> to create a random int ID
def randInt():
    return int(str(get_time()) + str(randint(0, 1000)))

# >> to generate random email
def randEmail():
    domain = 'random.com'
    length = 10
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return f'{username}@{domain}'

# >> to generate random password
def randPassw():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))

# endregion


# region | AES

# >> to encrypt into AES mode GCM
def enc(text):
    # creiamo il testo
    text = concatenate(text)
    text = randID(text, get_time(timelim=1000))

    # generiamo il salt per la chiave
    kdf_salt = get_random_bytes(16)

    # deriviamo la chiave
    key = PBKDF2(passphrase, kdf_salt)

    # creiamo l'oggetto cifrario AES in modalita GCM
    cipher = AES.new(key, AES.MODE_GCM)

    # cifriamo il testo
    cipher_text, tag = cipher.encrypt_and_digest(text.encode('utf-8'))

    # otteniamo il nonce utilizzato durante la cifratura
    nonce = cipher.nonce

    # costruiamo il messaggio formattato
    formatted_message = base64.b64encode(cipher_text).decode('utf-8') + delim + base64.b64encode(tag).decode('utf-8') + delim + base64.b64encode(nonce).decode('utf-8') + delim + base64.b64encode(kdf_salt).decode('utf-8')

    # aggiungiamo l'header al messaggio
    message = 'KSC01' + formatted_message

    return message

# >> to decrypt into AES mode GCM
def dec(message):
    # rimuoviamo l'header e separiamo
    message_components = message[3:].split(delim)

    # estraiamo i component dal messaggio formattato
    cipher_text = base64.b64decode(message_components[0])
    tag = base64.b64decode(message_components[1])
    nonce = base64.b64decode(message_components[2])
    kdf_salt = base64.b64decode(message_components[3])

    # deriviamo la chiave
    key = PBKDF2(passphrase, kdf_salt)

    # creiamo il cifrario AES in modalità GCM
    cipher = AES.new(key, AES.MODE_GCM, nonce)

    # decifriamo il testo cifrato e verifichiamo il tag/MAC
    try:
        decrypted_text = cipher.decrypt_and_verify(cipher_text, tag)
        return decrypted_text.decode('utf-8')
    except ValueError as e:
        return -1



# >> To encrypt into AES mode EAX
def encry_EAX(text):
    text = concatenate(text)
    text = randID(text, get_time(timelim=1000), [0, 10000]) # <--:: id contratto, id azienda, id utente, timestamp, id biglietto
    text_bytes = bytes(text, 'utf-8')

    cipher = AES.new(secret_key, AES.MODE_EAX)
    en_txt, tag = cipher.encrypt_and_digest(text_bytes)

    text_b64 = base64.b64encode(en_txt)
    b64_nonce = base64.b64encode(cipher.nonce)
    b64_tag = base64.b64encode(tag)

    txt = concatenate(['CAP01', str(b64_nonce, 'utf-8'), delim, str(b64_tag, 'utf-8'), delim, str(text_b64, 'utf-8')])
    return txt

# >> To decrypt from AES mode EAX
def decry_EAX(text):
    items = text.split(delim)
    #print(items)
    nonce = base64.b64decode(items[0])
    tag = base64.b64decode(items[1])
    txt = base64.b64decode(items[2])

    # > we create the object to decipher the text
    decipher = AES.new(secret_key, AES.MODE_EAX, nonce)

    # > we decipher the text
    deciph_txt = decipher.decrypt_and_verify(txt, tag)

    return str(deciph_txt, 'utf-8')


# >> To refresh (decry and encry)
def refresh(pnr):
    decoded_pnr = dec(pnr)
    encoded_pnr = enc(decoded_pnr)
    return encoded_pnr

# endregion

