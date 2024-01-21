"""
This will be used to collect manga pages from the using mangadex.org's API
"""
import requests
from collections import defaultdict
from google.cloud import storage
import time

filters = { "contentRating[]": ['safe','suggestive','erotica','pornographic']} 
# Filters is used to ensure that when we call the API we recieve all relevant titles regardless of content rating
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
    # filters = { "contentRating[]": ['safe','suggestive','erotica','pornographic'],} 

    for key,value in order.items():
        final_order[f"order[{key}]"] = value

    r = requests.get(base_url,
                     params = 
                     { 
                    **{"title":manga_name},
                    **final_order,
                    **filters
                               },
                     headers = {"Authorization":f"Bearer {bearer_token}"} )
    data = r.json()["data"]
    if r.status_code == 200 and len(data) !=0:
        return data[0]["id"]
    else:
        print("fail")
        return None
    


def get_chapters(manga_name, bearer_token, refresh_token, client_id, client_secret, limit = 100, offset = 0):
    # This function will be used to collect all chapters IDs which can then be used to download
    # We use limit and offset for the pagination of Mangadex's API

    id = get_id(manga_name, bearer_token)
    base_url = f"https://api.mangadex.org/manga/{id}/feed"
    hardcoded_stop = 0
    chapter_values = defaultdict(list)
    # structure for chapter_values:
    # language --> list of tuples (chap_number, ID)

    # We call the API which returns a limit of 100 items. We continue calling the api until we recieve an empty response which signifies that we've collected all the data.
    while hardcoded_stop <=50:
        try:
            r = requests.get(base_url, headers = {"Authorization":f"Bearer {bearer_token}"}, 
                            params = {"limit":limit, "offset":offset,
                                      **filters})
        except: 
            bearer_token = refresh(refresh_token, client_id, client_secret)
            r = requests.get(base_url, headers = {"Authorization":f"Bearer {bearer_token}"}, 
                            params = {"limit":limit, "offset":offset,
                                      **filters})

        # We check wether we've recived data due to pagination of the API
        if r.status_code == 200 and r.text: 
            data= r.json()
            if len(data['data'])!= 0:
                for value in data['data']:
                    if value['id'] is not None and value['attributes']['chapter'] is not None and value['attributes']['translatedLanguage'] is not None:
                        chapter_values[value['attributes']['translatedLanguage']].append( (value['attributes']['chapter'], value['id']) )
            else:
                break
                    
        else:
            break

        offset+=100
        hardcoded_stop+=1
    return chapter_values

def clean_and_sort(chapter_values):
    # Chapter values which has data structure:
    # language --> list of tuples (chap_number, ID)
    # Will have mutliple IDs of the same chapter since it is possible for many translations of the same manga to exist,
    # We will clean and remove all duplicate chapters and sort in acessending order

    for language in chapter_values:
        unique = dict()
        for tuple in chapter_values[language]:
            if tuple[0] not in unique:
                unique[tuple[0]] = tuple
        chapter_values[language] = list(unique.values())

        chapter_values[language] = sorted(chapter_values[language], key = lambda x:float(x[0]))
    return chapter_values

def download_manga(chapter_values, manga_name, bearer_token, refresh_token, client_id, client_secret):
    # This will be used to collect the urls for downloading chapters then downloading.
    # Since the download URLS have a relatively short lifespan, we must download one chapter by one chapter

    base_url = "https://api.mangadex.org/at-home/server/{chapterID}"
    download_urls = defaultdict(lambda: defaultdict(list)) 
    base_file_name = "{manga_name}/{language}/{chapter}/{panel}.png"
    # The structure for download urls will be:
    # language --> chapter_number --> list with download urls
    for language in chapter_values:
        for chapter,id in chapter_values[language]:
            url = base_url.format(chapterID=id)

            try:
                r = requests.get(url = url, headers = {"Authorization":f"Bearer {bearer_token}"})
            except:
                bearer_token = refresh(refresh_token, client_id, client_secret)
                print("token refreshed")
                r = requests.get(url = url, headers = {"Authorization":f"Bearer {bearer_token}"})

            if r.status_code == 200 and r.text: 
                data = r.json() 
                base = data['baseUrl']
                hash = data['chapter']['hash']
                panels_list = data['chapter']['data']
                
                for panel_num, panel in enumerate(panels_list):
                    # download_urls[language][chapter].append(base+ "/data/"+ hash+ "/"+ panel)
                    final_name = base_file_name.format(manga_name = manga_name,language = language, chapter = chapter, panel = str(panel_num))
                    upload_to_gcloud("manga_dataset_py", base+ "/data/"+ hash+ "/"+ panel, final_name, bearer_token)
                    
            else:
                print('error with request')
    
    return download_urls

def upload_to_gcloud(bucket_name, manga_url, destination_blob_name, bearer_token):
    # Used to upload to cloud without having to directly download on pc
    # Note, I have already authenticated using personal access token
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.content_type = 'image/png'
    # call API
    # I must use a rate limiting method since I will get an error if I do not
    hardcoded_stop = 0
    while hardcoded_stop <= 10:
        try:
            response = requests.get(manga_url, stream=True, headers = {"Authorization":f"Bearer {bearer_token}"})
            if response.status_code == 200:
                # Stream the content directly to Google Cloud Storage
                blob.upload_from_string(response.content, content_type="image/png")
                print(f"{destination_blob_name} uploaded to {bucket_name}.")
                break
            else:
                print(f"Failed to retrieve manga panel from {manga_url}")
        except:
            print("rate_limited" + " " +str(response.status_code))
            time.sleep(1)
        hardcoded_stop+=1
    
    