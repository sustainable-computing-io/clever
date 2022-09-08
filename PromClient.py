import time

import requests
import os
import json

requests.packages.urllib3.disable_warnings()

class PromClient:
    now = None
    start = None
    prom_address = "http://127.0.0.1:9090"
    prom_token = None
    step = '15s'
    chunk_sz = 900

    def __init__(self, prom_address=None, prom_token=None):
        self.prom_address = prom_address or os.getenv("PROM_HOST")
        self.prom_token = prom_token or os.getenv("PROM_TOKEN")

        if not self.prom_address:
            raise ValueError(
                "Please appropriately configure environment variables $PROM_HOST, $PROM_TOKEN to successfully run the crawler and profiler!")

    def get_query(self, my_query):
        try:
            if self.prom_token:
                headers = {"content-type": "application/json; charset=UTF-8",
                           'Authorization': 'Bearer {}'.format(self.prom_token)}
            else:
                headers = {"content-type": "application/json; charset=UTF-8"}
            response = requests.get('{0}/api/v1/query'.format(self.prom_address),
                                    params={'query': my_query},
                                    headers=headers, verify=False)
            print(response)

        except requests.exceptions.RequestException as e:
            print(e)
            return None

        try:
            if response.json()['status'] != "success":
                print("Error processing the request: " + response.json()['status'])
                print("The Error is: " + response.json()['error'])
                return None

            results = response.json()['data']['result']

            if (results is None):
                # print("the results[] came back empty!")
                return None

            length = len(results)
            if length > 0:
                return results
            else:
                # print("the results[] has no entries!")
                return None
        except:
            print(response)
            return None