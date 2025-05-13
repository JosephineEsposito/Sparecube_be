import os
import requests
import json
from utils.data import user

# class MailSender:
#     def send(self, subject, body, users, link=None):
#         raise NotImplementedError("This method must be overridden in subclasses")
#
#     def admin_send(self, subject, to_email, to_name, password, link=None):
#         raise NotImplementedError("This method must be overridden in subclasses")


class MailerSend:
    def __init__(self):
        self.api_key = os.getenv('MAILERSEND_API_KEY')
        self.from_email = os.getenv('EMAIL_SEND_SET')
        self.project_name = os.getenv('PROJECT', 'Sparecube')
        self.user_template_id = os.getenv('MAILERSEND_USER_TEMPLATE_ID', '3zxk54v71r64jy6v')
        self.admin_template_id = os.getenv('MAILERSEND_ADMIN_TEMPLATE_ID', '3yxj6lj1d27ldo2r')
        self.endpoint = "https://api.mailersend.com/v1/email"

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })

    def send(self, subject, body, users, link=None):
        to_list = [
            {
                "email": user["email"],
                "name": f"{user['first_name'].capitalize()} {user['last_name'].capitalize()}"
            }
            for user in users
        ]

        personalization = [
            {
                "email": user["email"],
                "data": {
                    "name": user["name"],
                    "text": body,
                    "link": link or ""
                }
            }
            for user in users
        ]

        payload = {
            "from": {"email": self.from_email, "name": self.project_name},
            "to": to_list,
            "subject": subject,
            "template_id": self.user_template_id,
            "personalization": personalization
        }

        return self._send_payload(payload)

    def admin_send(self, subject, to_email, to_name, password, link=None):

        payload = {
            "from": {"email": self.from_email, "name": self.project_name},
            "to": [{"email": to_email, "name": to_name}],
            "subject": subject,
            "template_id": self.admin_template_id,
            "personalization": [{
                "email": to_email,
                "data": {
                    "name": to_name,
                    "password": password,
                    "link": link or ""
                }
            }]
        }

        return self._send_payload(payload)

    def _send_payload(self, payload):
        try:
            response = self.session.post(self.endpoint, data=json.dumps(payload))
            response.raise_for_status()
            return {"status": 0, "response": response.json()}
        except requests.exceptions.RequestException as e:
            print(f"MailerSend error: {e}")
            return {"status": 1, "error": str(e)}



class MailChimp:
    def __init__(self):
        self.api_key = os.getenv('MAILCHIMP_API_KEY_NEW')
        self.from_email = os.getenv('EMAIL_SEND_SPARECUBE')
        self.project_name = os.getenv('PROJECT', 'Sparecube')
        self.template_name = os.getenv('MAILCHIMP_TEMPLATE', 'sparecube')
        self.endpoint = "https://mandrillapp.com/api/1.0/messages/send-template.json"

    def send(self, subject, body, users, link=None):
        to_list = []
        for new_user in users:
            if isinstance(new_user, dict):
                user_data = user.User(new_user)
            else:
                user_data = new_user
            #user_data = user.User(new_user)
            to_list.append({
                "email": user_data.email,
                "name": f"{user_data.first_name.capitalize()} {user_data.last_name.capitalize()}",
            })

        print("to_list: ", to_list)

        merge_vars = []
        for new_user in users:
            if isinstance(new_user, dict):
                user_data = user.User(new_user)
            else:
                user_data = new_user
           # user_data = user.User(new_user)
            merge_vars.append({
                "rcpt": user_data.email,
                "vars": [
                    {"name": "name", "content": f"{user_data.first_name.capitalize()} {user_data.last_name.capitalize()}"},
                    {"name": "body", "content": body},
                    {"name": "link", "content": link or ""}
                ]
            })

            print("merge_vars: ", merge_vars)


        payload = {
            "key": self.api_key,
            "template_name": self.template_name,
            "template_content": [],
            "message": {
                "subject": subject,
                "from_email": self.from_email,
                "from_name": self.project_name,
                "to": to_list,
                "merge": True,
                "merge_language": "mailchimp",
                "global_merge_vars": [],
                "merge_vars": merge_vars
            }
        }

        print("payload: ", payload)


        try:
            response = requests.post(self.endpoint, json=payload)

            print("response: ", response)

            response.raise_for_status()
            results = response.json()

            print("results: ", results)

            for result in results:
                print(f"Email: {result.get('email')}, Status: {result.get('status')}, Reason: {result.get('reject_reason')}")

            return {"status": 0, "response": results}
        except requests.RequestException as e:
            print(f"MailChimp error: {e}")
            return {"status": 1, "error": str(e)}



# """
# Email Sender Manager
# """
#
# import os
#
# # MAILERSEND EMAIL MANAGEMENT
# from mailersend import emails
#
# def send(oggetto, corpo, emails_list, names_list, link=None):
#     mailer = emails.NewEmail(os.environ['MAILERSEND_API_KEY'])
#
#     mail_body = {}
#
#     mail_from = {
#         "name": os.environ['PROJECT'],
#         "email": os.environ['EMAIL_SEND'],
#     }
#
#     recipients = []
#     variables = []
#
#     for email, nome in zip(emails_list, names_list):
#         recipients.append({
#             "name": nome,
#             "email": email,
#         })
#
#         variables.append({
#             "email": email,
#             "data": {
#                 "name": nome,
#                 "text": corpo,
#                 "link": link or ""
#             }
#         })
#
#     mailer.set_mail_from(mail_from, mail_body)
#     mailer.set_mail_to(recipients, mail_body)
#     mailer.set_subject(oggetto, mail_body)
#     mailer.set_template("3zxk54v71r64jy6v", mail_body)
#     mailer.set_personalization(variables, mail_body)
#
#     result = mailer.send(mail_body)
#     print("result", result)
#
#     return {"status": 0}
#
#
# # def send(oggetto, corpo, email, nome, link = None):
# #     mailer = emails.NewEmail(os.environ['MAILERSEND_API_KEY'])
# #     print("email", email)
# #
# #     mail_body = {}
# #
# #     mail_from = {
# #         "name" : os.environ['PROJECT'],
# #         "email": os.environ['EMAIL_SEND'],
# #     }
# #
# #     recipients = [
# #         {
# #             "name" : nome,
# #             "email": email,
# #         }
# #     ]
# #
# #     variables = [
# #         {
# #             "email": email,
# #             "data": {
# #                 "name": nome,
# #                 "text": corpo,
# #                 "link": link or ""
# #             }
# #         }
# #     ]
# #
# #     # variables = [
# #     #     {
# #     #         "email" : email,
# #     #         "substitutions" : [
# #     #             {
# #     #                 "var" : "name",
# #     #                 "value" : nome
# #     #             },
# #     #             {
# #     #                 "var": "text",
# #     #                 "value": corpo
# #     #             },
# #     #             {
# #     #                 "var" : "link",
# #     #                 "value": link
# #     #             }
# #     #         ]
# #     #     }
# #     # ]
# #
# #     # substitutions = [
# #     #     {"var": "name", "value": nome},
# #     #     {"var": "text", "value": corpo},
# #     #     {"var": "link", "value": link or ""}
# #     # ]
# #     #
# #     # personalization = [
# #     #     {
# #     #         "email": email,
# #     #         "substitutions": substitutions
# #     #     }
# #     # ]
# #
# #     mailer.set_mail_from(mail_from, mail_body)
# #     mailer.set_mail_to(recipients, mail_body)
# #     mailer.set_subject(oggetto, mail_body)
# #     mailer.set_template("3zxk54v71r64jy6v", mail_body)
# #     #mailer.set_simple_personalization(variables, mail_body)
# #     mailer.set_personalization(variables, mail_body)
# #
# #     x = mailer.send(mail_body)
# #     print ("result", x)
# #
# #
# #     return {"status" : 0}
#
# def admin_send(oggetto, email, nome, password, link = None):
#
#     mailer = emails.NewEmail(os.environ['MAILERSEND_API_KEY'])
#
#     mail_body = {}
#
#     mail_from = {
#         "name" : os.environ['PROJECT'],
#         "email": os.environ['EMAIL_SEND'],
#     }
#
#     recipients = [
#         {
#             "name" : nome,
#             "email": email,
#         }
#     ]
#
#     variables = [
#         {
#             "email" : email,
#             "substitutions" : [
#                 {
#                     "var" : "name",
#                     "value" : nome
#                 },
#                 {
#                     "var": "password",
#                     "value": password
#                 },
#                 {
#                     "var" : "link",
#                     "value": link
#                 }
#             ]
#         }
#     ]
#
#     mailer.set_mail_from(mail_from, mail_body)
#     mailer.set_mail_to(recipients, mail_body)
#     mailer.set_subject(oggetto, mail_body)
#     mailer.set_template("3yxj6lj1d27ldo2r", mail_body)
#     mailer.set_simple_personalization(variables, mail_body)
#
#     mailer.send(mail_body)
#
#     return {"status" : 0}
#
