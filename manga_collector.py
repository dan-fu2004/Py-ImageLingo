"""
This will be used to collect manga pages from the using mangadex.org's API
"""
import requests
from collections import defaultdict
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
    # Used to get the ID given the manga_name
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


def get_chapters(manga_name, bearer_token, refresh_token, client_id, client_secret, limit = 100, offset = 0):
    # This function will be used to collect all chapters IDs which can then be used to download
    # We use limit and offset for the pagination of Mangadex's API

    id = get_id(manga_name, bearer_token)
    base_url = f"https://api.mangadex.org/manga/{id}/feed"
    hardcoded_stop = 0
    chapter_values = defaultdict(list)
    # structure for chapter_values:
    # language --> list with ids

    # We call the API which returns a limit of 100 items. We continue calling the api until we recieve an empty response which signifies that we've collected all the data.
    while hardcoded_stop <=50:
        try:
            r = requests.get(base_url, headers = {"Authorization":f"Bearer {bearer_token}"}, 
                            params = {"limit":limit, "offset":offset})
        except: 
            bearer_token = refresh(refresh_token, client_id, client_secret)
            r = requests.get(base_url, headers = {"Authorization":f"Bearer {bearer_token}"}, 
                            params = {"limit":limit, "offset":offset})

        # We check wether we've recived data due to pagination of the API
        if r.status_code == 200 and r.text: 
            data= r.json()
            for value in data['data']:
                if value['id'] is not None and value['attributes']['chapter'] is not None and value['attributes']['translatedLanguage'] is not None:
                    chapter_values[value['attributes']['translatedLanguage']].append( (value['attributes']['chapter'], value['id']) )
                    
        else:
            break

        offset+=100
        hardcoded_stop+=1
    return chapter_values


def download_manga(chapter_values, bearer_token, refresh_token, client_id, client_secret):
    # This will be used to collect the urls for downloading chapters then downloading.
    # Since the download URLS have a relatively short lifespan, we must download one chapter by one chapter

    base_url = "https://api.mangadex.org/at-home/server/{chapterID}"
    download_urls = defaultdict(lambda: defaultdict(list)) 
    # The structure for download urls will be:
    # language --> chapter_number --> list with download urls
    for language in chapter_values:
        for chapter,id in chapter_values[language]:
            url = base_url.format(chapterID=id)

            try:
                r = requests.get(url = url, headers = {"Authorization":f"Bearer {bearer_token}"})
            except:
                bearer_token = refresh(refresh_token, client_id, client_secret)
                r = requests.get(url = url, headers = {"Authorization":f"Bearer {bearer_token}"})

            if r.status_code == 200 and r.text: 
                data = r.json() 
                base = data['baseUrl']
                hash = data['chapter']['hash']
                panels_list = data['chapter']['data']
                
                for panel in panels_list:
                    download_urls[language][chapter].append(base+ "/data/"+ hash+ "/"+ panel)
                    # note chapter here is a string representing the chapter number
    
    
    return download_urls