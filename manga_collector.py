"""
This will be used to collect manga pages from the using mangadex.org's API
"""
import requests

def authenticate(username, password, client_id, client_secret, grant_type = "password"):
    url = "https://auth.mangadex.org/realms/mangadex/protocol/openid-connect/token"
    try:
        r = requests.post(url, 
        data = {"grant_type": grant_type,
                "username":username,
                "password":password,
                "client_id":client_id,
                "client_secret":client_secret
        },
        headers = {'Content-Type': 'application/x-www-form-urlencoded'},)

        if r.status_code == 200:
            data = r.json()
            bearer_token = data["access_token"]
            refresh = data["refresh_token"]   
            return (bearer_token,refresh)
    except:
        print("error")

def refresh(refresh_token, client_id, client_secret, grant_type ='refresh_token'):
    url = 'https://auth.mangadex.org/realms/mangadex/protocol/openid-connect/token/auth/refresh'
    r = requests.post(url, 
    data = 
    {
        "grant_type": grant_type,
        "refresh_token":refresh_token,
        "client_id":client_id,
        "client_secret":client_secret
     })
    if r.status_code == 200:
        data = r.json()
        return data["access_token"]
            

def get_secret(client_id, bearer_token):
    url = "https://api.mangadex.org/client/{id}/secret"
    url.format(id = client_id)
    r = requests.get(url)
    print(r.status_code)
    return r
    


def get_id(manga_name, bearer_token):
    base_url = "https://api.mangadex.org/manga"
    order = {
    # "relevance":"desc"
    }
    final_order = {}
    for key,value in order.items():
        final_order[f"order[{key}]"] = value

    r = requests.get(base_url,
                     params = 
                     { 
                    **{"title":manga_name},
                    **final_order
                               },
                     headers = {"Authorization":f"Bearer {bearer_token}"} )
    
    data = r.json()["data"]
    return data[0]["id"]


def download_manga(manga_name, bearer_token):
    id = get_id(manga_name, bearer_token)
    base_url = f"https://api.mangadex.org/manga/{id}/feed"
    r = requests.get(base_url, headers = {"Authorization":f"Bearer {bearer_token}"})
    data = r.json()
    print(data)
    return data





