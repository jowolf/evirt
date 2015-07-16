import hashlib, random
import settings


class TokenAuth (object):
    def __init__ (self):
        self.token = ''
        self.hashed_secret = hashlib.sha224 (`settings.shared_secret`).hexdigest()
        #self.ip =
        # check ip against hashed secret for me
        # self.caller_ip =

    def get_auth_token (self, hashed_secret):
        assert hashlib.sha224 (`settings.shared_secret`).hexdigest() == hashed_secret

        curr_token = hashlib.sha224 (hashed_secret + `random.random()`).hexdigest()
        #last_token = curr_token
        return curr_token


    # 'Rotates' to the next token - called from  core.SecureTransport.request in the client
    def next_token (self):      # returns next valid token, or None if no match
        if self.token:
            self.token = hashlib.sha224 (`settings.shared_secret` + self.token).hexdigest()
        else:
            self.token = hashlib.sha224 (self.hashed_secret + `random.random()`).hexdigest()

        return self.token


    # Start or rotate to next - Called from SecureJSONRPCRequestHandler.do_POST on the server
    def verify_token (self, token):  # checks and rotates
        if token == self.token:  # its ok, generate next
            self.token = hashlib.sha224 (`settings.shared_secret` + self.curr_token).hexdigest()
            return True
        elif token == self.hashed_secret:
            self.token = hashlib.sha224 (self.hashed_secret + `random.random()`).hexdigest()
            # check IP address here for caller
            return True


    #def add_header
    #def check_header


# Exported convenience singleton
token_auth = TokenAuth()