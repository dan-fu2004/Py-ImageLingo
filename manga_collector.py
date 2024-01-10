"""
This will be used to collect manga pages from the using mangadex.org's API
"""
import requests
import json

def authenticate(username, password, client_id, cilent_secret, grant_type = 'password'):
    url = 'https://auth.mangadex.org/realms/mangadex/protocol/openid-connect/token'
    
    r = requests.post(url, 
    params = {"grant_type": grant_type,
            "username":username,
            "password":password,
            "client_id":client_id,
            "client_secret":client_secret
     })
    


def get_id(manga_name:str):
    base_url = "https://api.mangadex.org/manga"
    r = requests.get(base_url,
                     params = {"title":manga_name})
    print([manga["id"] for manga in r.json()["data"]])



get_id('Chainsaw Man')