from srna_api.extensions import oidc
import requests
from flask import json, jsonify, Response
from srna_api.models.user import User, UserSchema
import datetime

user_schema = UserSchema(many=False)

class UserKeycloak():


    def obtain_keycloak_token(self):
        r = []
        user = oidc.client_secrets['keycloak_username']
        pwd = oidc.client_secrets['keycloak_pwd']
        cs = oidc.client_secrets['client_secret']
        url = oidc.client_secrets['keycloak_uri_master']
        payload = {"realm": "master",
                    "bearer-only": "true",
                    "client_id": "admin-cli",
                    "username": user,
                    "password": pwd,
                    "grant_type": "password",
                    "client_secret": cs}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(url, headers=headers, data=payload)
        if response.status_code == 200:
            r = response.json()
        return r

    def get_user_keycloak(self, username):
        url = oidc.client_secrets["keycloak_uri_srna"]

        if username:
            url = url + '?username='+ username

        token = self.obtain_keycloak_token()

        if token:
            bearer_token = 'Bearer ' + token['access_token']
            headers = {'Authorization': bearer_token}

            response = requests.get(url, headers=headers)

        return response


    def obtain_payload_keycloak(self,data):

        email = ''
        if 'Email' in data and type(data['Email'])==str:
            email = data['Email']

        user = {"username": data["User Name"],
                "enabled": "true",
                "totp": "false",
                "emailVerified": "false",
                "firstName": data["First Name"],
                "lastName": data["Last Name"],
                "disableableCredentialTypes": [],
                "requiredActions": [],
                "notBefore": 0,
                "email" : email,
                "access": {
                    "manageGroupMembership": "true",
                    "view": "true",
                    "mapRoles": "true",
                    "impersonate": "true",
                    "manage": "true"
                },
                "credentials": [{
                    "type": "password",
                    "temporary": "true",
                    "value": data["Password"]
                 }]
                }
        payload = json.dumps(user)
        return payload


    def __add_one_user_keycloak(self, url, payload, token):
        bearer_token = 'Bearer ' + token['access_token']
        headers = {'Authorization': bearer_token,
            'Content-Type': 'application/json'}
        response = requests.post(url, headers=headers, data=payload)
        return response.status_code




    def import_user(self, user, token):
        try:
            count = 0
            status_code = 401
            max_attempts = 2
            url = oidc.client_secrets["keycloak_uri_srna"]
            payload = self.obtain_payload_keycloak(user)

            if not token:
                token = self.obtain_keycloak_token()

            if token:
                while (status_code == 401) and (count < max_attempts):
                    status_code = self.__add_one_user_keycloak(url, payload, token)

                    # Ask for another token, if expired
                    if not ((status_code) >= 200 and (status_code) <= 300):
                        token = self.obtain_keycloak_token()
                        count = count + 1

                if ((status_code) >= 200 and (status_code) <= 300):
                        user['kc_import'] = "Imported"
                else:
                    if status_code==409:
                        user['kc_import'] = "Username or email already exists"
                    else:
                        user['kc_import'] = "Error: " + str(status_code)
            else:
                user['kc_import'] = "Not imported. Keycloak token couldn't be retrieved."
        except Exception as e:
            user['kc_import'] = "Error: " + str(e)

        user['kc_status_code'] = status_code
        return token


    def reset_user_password(self, user, data):
        try:
            status_code = 403
            password = data['password']
            #Obtain keycloak token
            token = self.obtain_keycloak_token()
            if token:
                #Obtain keycloak userid
                response = self.get_user_keycloak(user.name)
                status_code = response.status_code
                if response.status_code >= 200 and response.status_code<=300:
                    #Make call to change password of user
                    data = response.json()
                    if len(data)>0:
                        user_keycloak_id = data[0]['id']
                        url = oidc.client_secrets["keycloak_uri_srna"] + '/'+ user_keycloak_id + '/reset-password'
                        p = {"type": "password",
                             "temporary": "true",
                              "value": password
                            }
                        payload = json.dumps(p)
                        bearer_token = 'Bearer ' + token['access_token']
                        headers = {'Authorization': bearer_token,
                               'Content-Type': 'application/json'}
                        response = requests.put(url, headers=headers, data=payload)
                        status_code = response.status_code
                    else:
                        status_code = 404
        except Exception as e:
             status_code = 400

        return status_code


    def get_client_id(self, realm):

        id = ''
        url = oidc.client_secrets["keycloak_uri_srna_base"] + '/clients/'

        token = self.obtain_keycloak_token()

        if token:
            bearer_token = 'Bearer ' + token['access_token']
            headers = {'Authorization': bearer_token}
            response = requests.get(url, headers=headers)

            if response.status_code>=200 and response.status_code<=300:
                response_json = response.json()

                for data in response_json:
                    if data['clientId']==realm:
                        id=data['id']
                        break

        return id

    def user_session_response(self, data):
        user_sessions = []

        for d in data:
            user_db = User.query.filter_by(name=d.get('username')).first()
            user= user_schema.dump(user_db)
            sdt = datetime.datetime.fromtimestamp(float(d["start"]) / 1000.0)  #Convert from ms to datetime
            user["start_datetime"] = sdt.strftime('%Y-%m-%dT%H:%M:%S.%f')
            ladt = datetime.datetime.fromtimestamp(float(d["lastAccess"]) / 1000.0)
            user["last_access_datetime"] = ladt.strftime('%Y-%m-%dT%H:%M:%S.%f')
            user_sessions.append(user)

        return user_sessions


    def get_user_sessions(self, realm, first, max):

        user_sessions=''
        #Get id for client_id (id <> client_id)
        id = self.get_client_id(realm)

        if len(id)>0:
            if first and max:
                url = oidc.client_secrets["keycloak_uri_srna_base"] + '/clients/' + id + '/user-sessions?first='+str(first)+'&max='+str(max)
            else:
                url = oidc.client_secrets["keycloak_uri_srna_base"] + '/clients/' + id + '/user-sessions'

            #Get token
            token = self.obtain_keycloak_token()

            if token:
                bearer_token = 'Bearer ' + token['access_token']
                headers = {'Authorization': bearer_token}

                response = requests.get(url, headers=headers)
                if response.status_code >= 200 and response.status_code <= 300:
                    response_json = response.json()
                    user_sessions = self.user_session_response(response_json)

        return user_sessions


    def get_user_sessions_count(self, realm):
        count = ''
        # Get id for client_id (id <> client_id)
        id = self.get_client_id(realm)

        if len(id) > 0:
            url = oidc.client_secrets["keycloak_uri_srna_base"] + '/clients/' + id + '/session-count'

            # Get token
            token = self.obtain_keycloak_token()

            if token:
                bearer_token = 'Bearer ' + token['access_token']
                headers = {'Authorization': bearer_token}

                response = requests.get(url, headers=headers)
                if response.status_code>=200 and response.status_code<=300:
                    count = response.json()

        return count
