#!/bin/bash

HOSTNAME=$1
REALM_NAME=$2
USERNAME=$3
CLIENT_ID=$4
CLIENT_SECRET=$5
HTTP=$6
SECURE=$7

if [[ $HTTP != 'y' ]]; then
    PROTOCOL="HTTPS"
    HTTP='n'
else
    PROTOCOL="HTTP"
fi

KEYCLOAK_URL="$PROTOCOL://$HOSTNAME/auth/realms/$REALM_NAME/protocol/openid-connect/token"

if [[ $SECURE == 'y' ]]; then
	INSECURE=
else 
	INSECURE=--insecure
    SECURE='n'
fi

echo "Using Keycloak: $KEYCLOAK_URL"
echo "realm: $REALM_NAME"
echo "client-id: $CLIENT_ID"
echo "username: $USERNAME"
echo "secret: $CLIENT_SECRET"
echo "http: $HTTP"
echo "secure: $SECURE"

echo -n Password: 
read -s PASSWORD

TOKEN=$(curl -X POST "$KEYCLOAK_URL" "$INSECURE" \
 -H "Content-Type: application/x-www-form-urlencoded" \
 -d "username=$USERNAME" \
 -d "password=$PASSWORD" \
 -d 'grant_type=password' \
 -d "client_id=$CLIENT_ID" \
 -d "client_secret=$CLIENT_SECRET")

echo "$TOKEN"

export TOKEN