import hashlib
import settings


class TokenAuth (object):
    def __init__ (self):
        self.curr_token = ''
        #self.last_token = ''

    def get_auth_token (self, hashed_secret):
        assert hashlib.sha224 (`settings.shared_secret`).hexdigest() == hashed_secret

        curr_token = hashlib.sha224 (hashed_secret + `random.random()`).hexdigest()
        #last_token = curr_token
        return curr_token


    # 'Rotates' to the next token
    # Called fm SecureJSONRPCRequestHandler.do_POST on the server, and core.SecureTransport.send_contents in the client
    def get_next_token (self, curr_token):      # returns next valid token, or None if no match
        if curr_token == self.curr_token:
            curr_token = hashlib.sha224 (`settings.shared_secret` + self.curr_token).hexdigest()
            return curr_token

    #def add_header
    #def check_header


# Exported convenience singleton
token_auth = TokenAuth()