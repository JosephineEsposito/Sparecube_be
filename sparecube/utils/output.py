
class Output:
    def __init__(self):
        data = []
        errors = []
        message = ""
        result = None

    # ========== SET ========== #
    def setData(self, d):
        self.data.append(d)

    def setErrors(self, e):
        self.errors.append(e)
    
    def setMessage(self, m):
        self.message = m

    def setResult(self, r):
        self.result = r

    # ========== MAS ========== #
    def clean(self):
        self.data = []
        self.errors = []
        self.message = ""
        self.result = None

    def json(self):
        resp = {}
        if self.data:
            if len(self.data) == 1:
                resp["data"] = self.data[0]
            else:
                resp["data"] = self.data
        
        if self.errors:
            if len(self.errors) == 1:
                resp["errors"] = self.errors[0]
            else:
                resp["errors"] = self.errors

        if self.message:
            resp["message"] = self.message

        if self.result != None:
            if self.result == 0:
                resp['result'] = self.result
            else:
                resp['result'] = -1
        
        return resp
    
    #region | messaggi custom
    def permissionDenied(self):
        self.message = 'Non si dispone dei permessi necessari per effettuare questa azione.'
    
    def dbError(self):
        self.message = 'Errore nella connessione con il database.'
    #endregion
