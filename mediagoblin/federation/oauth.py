# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011, 2012 MediaGoblin contributors.  See AUTHORS.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from oauthlib.common import Request
from oauthlib.oauth1 import (AuthorizationEndpoint, RequestValidator, 
                             RequestTokenEndpoint, AccessTokenEndpoint)

from mediagoblin.db.models import NonceTimestamp, Client, RequestToken, AccessToken



class GMGRequestValidator(RequestValidator):

    enforce_ssl = False

    def __init__(self, data=None):
        self.POST = data

    def save_request_token(self, token, request):
        """ Saves request token in db """
        client_id = self.POST[u"oauth_consumer_key"]

        request_token = RequestToken(
                token=token["oauth_token"],
                secret=token["oauth_token_secret"],
                )
        request_token.client = client_id
        request_token.callback = token.get("oauth_callback", None)
        request_token.save()

    def save_verifier(self, token, verifier, request):
        """ Saves the oauth request verifier """
        request_token = RequestToken.query.filter_by(token=token).first()
        request_token.verifier = verifier["oauth_verifier"]
        request_token.save()

    def save_access_token(self, token, request):
        """ Saves access token in db """
        access_token = AccessToken(
                token=token["oauth_token"],
                secret=token["oauth_token_secret"],
        )
        access_token.request_token = request.oauth_token
        request_token = RequestToken.query.filter_by(token=request.oauth_token).first()
        access_token.user = request_token.user
        access_token.save()

    def get_realms(*args, **kwargs):
        """ Currently a stub - called when making AccessTokens """
        return list()

    def validate_timestamp_and_nonce(self, client_key, timestamp, 
                                     nonce, request, request_token=None, 
                                     access_token=None):
        nc = NonceTimestamp.query.filter_by(timestamp=timestamp, nonce=nonce)
        nc = nc.first()
        if nc is None:
            return True
        
        return False

    def validate_client_key(self, client_key, request):
        """ Verifies client exists with id of client_key """
        client = Client.query.filter_by(id=client_key).first()
        if client is None:
            return False
        
        return True

    def validate_access_token(self, client_key, token, request):
        """ Verifies token exists for client with id of client_key """
        client = Client.query.filter_by(id=client_key).first()
        token = AccessToken.query.filter_by(token=token)
        token = token.first()

        if token is None:
            return False

        request_token = RequestToken.query.filter_by(token=token.request_token)
        request_token = request_token.first()

        if client.id != request_token.client:
            return False

        return True

    def validate_realms(self, *args, **kwargs):
        """ Would validate reals however not using these yet. """
        return True # implement when realms are implemented


    def get_client_secret(self, client_key, request):
        """ Retrives a client secret with from a client with an id of client_key """
        client = Client.query.filter_by(id=client_key).first()
        return client.secret

    def get_access_token_secret(self, client_key, token, request):
        client = Client.query.filter_by(id=client_key).first()
        access_token = AccessToken.query.filter_by(token=token).first()
        return access_token.secret

class GMGRequest(Request):
    """
        Fills in data to produce a oauth.common.Request object from a
        werkzeug Request object
    """

    def __init__(self, request, *args, **kwargs):
        """ 
            :param request: werkzeug request object
            
            any extra params are passed to oauthlib.common.Request object
        """
        kwargs["uri"] = kwargs.get("uri", request.url)
        kwargs["http_method"] = kwargs.get("http_method", request.method)
        kwargs["body"] = kwargs.get("body", request.get_data())
        kwargs["headers"] = kwargs.get("headers", dict(request.headers))

        super(GMGRequest, self).__init__(*args, **kwargs)
