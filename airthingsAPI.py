import logging
import requests
import json
from requests import HTTPError
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from azure.eventhub import EventHubProducerClient, EventData, TransportType


def getAirThings():

    ## Get secrets
    credential = DefaultAzureCredential()
    vaulturl = 'https://.vault.azure.net'
    client = SecretClient(vault_url = vaulturl , credential=credential)

    client_secret = (client.get_secret('clientsecret')).value
    device_id = (client.get_secret('deviceid')).value
    client_id = (client.get_secret('clientid')).value

    connectionString = (client.get_secret('eventHub')).value
    eventHubName = (client.get_secret('eventhubname')).value

    ## ViewPlus API
    authorisation_url = 'https://accounts-api.airthings.com/v1/token'
    device_url = f'https://ext-api.airthings.com/v1/devices/{device_id}/latest-samples'
    token_req_payload = {
        'grant_type': 'client_credentials',
        'scope': 'read:device:current_values',
    }

    # Get token
    try:
        token_response = requests.post(
            authorisation_url,
            data = token_req_payload,
            allow_redirects = False,
            auth = (client_id, client_secret),
        )

    except HTTPError as error:
        logging.error(error)

    token = token_response.json()['access_token']


    # Get ViewPlus data
    try:
        api_headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(url = device_url, headers = api_headers)
    except HTTPError as error:
        logging.error(error)

    # Data
    transformed_data = {
        'CO2': response.json()['data']['co2'],
        'Humidity': response.json()['data']['humidity'],
        'PM1': response.json()['data']['pm1'],
        'PM25': response.json()['data']['pm25'],
        'Pressure': response.json()['data']['pressure'],
        'Radon': response.json()['data']['radonShortTermAvg'],
        'VOC': response.json()['data']['voc'],
        'Time': response.json()['data']['time']
    }

    ## Azure EvenHub
    producer = EventHubProducerClient.from_connection_string(
        conn_str = connectionString, 
        eventhub_name = eventHubName, 
        transport_type = TransportType.AmqpOverWebsocket
    )
    

    event_data = json.dumps(transformed_data)
    event_to_send = EventData(event_data)
    event_batch = producer.create_batch()
    event_batch.add(event_to_send)
    producer.send_batch(event_batch)






 