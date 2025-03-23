"""
Email Sender Manager
"""

import os

# MAILERSEND EMAIL MANAGEMENT
from mailersend import emails



def send(oggetto, corpo, email, nome, link = None):
    mailer = emails.NewEmail(os.environ['MAILERSEND_API_KEY'])

    mail_body = {}

    mail_from = {
        "name" : os.environ['PROJECT'],
        "email": os.environ['EMAIL_SEND'],
    }

    recipients = [
        {
            "name" : nome,
            "email": email,
        }
    ]

    variables = [
        {
            "email" : email,
            "substitutions" : [
                {
                    "var" : "name",
                    "value" : nome
                },
                {
                    "var": "text",
                    "value": corpo
                },
                {
                    "var" : "link",
                    "value": link
                }
            ]
        }
    ]

    mailer.set_mail_from(mail_from, mail_body)
    mailer.set_mail_to(recipients, mail_body)
    mailer.set_subject(oggetto, mail_body)
    mailer.set_template("3zxk54v71r64jy6v", mail_body)
    mailer.set_simple_personalization(variables, mail_body)
    
    mailer.send(mail_body)

    return {"status" : 0}

def admin_send(oggetto, email, nome, password, link = None):
    
    mailer = emails.NewEmail(os.environ['MAILERSEND_API_KEY'])

    mail_body = {}

    mail_from = {
        "name" : os.environ['PROJECT'],
        "email": os.environ['EMAIL_SEND'],
    }

    recipients = [
        {
            "name" : nome,
            "email": email,
        }
    ]

    variables = [
        {
            "email" : email,
            "substitutions" : [
                {
                    "var" : "name",
                    "value" : nome
                },
                {
                    "var": "password",
                    "value": password
                },
                {
                    "var" : "link",
                    "value": link
                }
            ]
        }
    ]

    mailer.set_mail_from(mail_from, mail_body)
    mailer.set_mail_to(recipients, mail_body)
    mailer.set_subject(oggetto, mail_body)
    mailer.set_template("3yxj6lj1d27ldo2r", mail_body)
    mailer.set_simple_personalization(variables, mail_body)
    
    mailer.send(mail_body)

    return {"status" : 0}

