"""
Manager of user data
"""

class User():
    def __init__(self, args = None):
        if args is None:
            # default values for attributes if args is not provided
            self.id             = None
            self.id_azienda     = None
            self.first_name     = None
            self.last_name      = None
            self.username       = None
            self.email          = None
            self.account_type   = None
            self.is_active      = None
            self.is_staff       = None
            self.is_superuser   = None
        else:
            # initialize attributes with values from args dictionary
            self.id             = args.get("id")
            self.id_azienda     = args.get("id_azienda")
            self.first_name     = args.get("first_name")
            self.last_name      = args.get("last_name")
            self.username       = args.get("username")
            self.email          = args.get("email")
            self.account_type   = args.get("account_type")
            self.is_active      = args.get("is_active")
            self.is_staff       = args.get("is_staff")
            self.is_superuser   = args.get("is_superuser")
    

    def json(self):
        utente = {
            "id"            : self.id,
            "name"          : self.first_name + " " + self.last_name,
            "username"      : self.username,
            "email"         : self.email,
            "account_type"  : self.account_type,
            "id_azienda"    : self.id_azienda,
            "is_active"     : self.is_active,
            "is_staff"      : self.is_staff,
            "is_superuser"  : self.is_superuser,
        }
        return utente
    
    def clean(self):
        self.id             = None
        self.id_azienda     = None
        self.first_name     = None
        self.last_name      = None
        self.username       = None
        self.email          = None
        self.account_type   = None
        self.is_active      = None
        self.is_staff       = None
        self.is_superuser   = None

    def base(self):
        return {
            "id"            : 0,
            "id_azienda"    : 0,
            "first_name"    : "",
            "last_name"     : "",
            "username"      : "",
            "email"         : "",
            "account_type"  : "",
            "is_active"     : 0,
            "is_staff"      : 0,
            "is_superuser"  : 0
        }
