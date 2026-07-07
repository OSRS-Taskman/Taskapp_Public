import os
import pymongo
import base64

def create_pem_from_base64(base64_string, filename):
    # if certificate already exists, return
    if os.path.exists(filename):
        return
    
    decoded_data = base64.b64decode(base64_string)

    # save to file
    with open(filename, "wb") as pem_file:
        pem_file.write(decoded_data)

IS_PROD = os.environ["FLASK_ENV"].lower() != "development"
SECRET_KEY = os.environ["SECRET_KEY"]
SENDGRID_API_KEY = os.environ["SENDGRID_API_KEY"]
MONGO_URL = os.environ["MONGO_URI"]
DISCORD_CLIENT_ID = os.environ["DISCORD_CLIENT_ID"]
DISCORD_CLIENT_SECRET = os.environ["DISCORD_CLIENT_SECRET"]
DISCORD_REDIRECT_URI = os.environ["DISCORD_REDIRECT_URI"]

if IS_PROD:
    RECAPTCHA_SITE_KEY = os.environ["RECAPTCHA_SITE_KEY"]
    RECAPTCHA_SECRET_KEY = os.environ["RECAPTCHA_SECRET_KEY"]
    X509_CERT = os.environ["X509"]
    create_pem_from_base64(X509_CERT, "certificate.pem")
    MONGO_CLIENT = pymongo.MongoClient(MONGO_URL,
                                       tls=True,
                                       tlsCertificateKeyFile="certificate.pem")
else:
    if os.path.exists("certificate.pem"):
        MONGO_CLIENT = pymongo.MongoClient(MONGO_URL,
                                       tls=True,
                                       tlsCertificateKeyFile="certificate.pem")
    else:
        MONGO_CLIENT = pymongo.MongoClient(MONGO_URL)
