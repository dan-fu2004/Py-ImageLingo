import os
from concurrent.futures import ThreadPoolExecutor
from manga_collector import *

import logging

# Basic configuration for logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def download_manga_local(chapter_values, manga_name, client_id, client_secret, refresh_token, base_directory):
    global bearer_token
    base_url = "https://api.mangadex.org/at-home/server/{chapterID}"
    base_file_name = "{manga_name}/{language}/{chapter}/{panel}.{type}"



    for language in chapter_values:
        with ThreadPoolExecutor(max_workers=10) as executor:
            for chapter, id in chapter_values[language]:
                futures = []
                print(chapter)
                # print(f"Starting download for {manga_name} in {language}, chapter: {chapter}")
                auto_refresh_token(refresh_token, client_id, client_secret)
                url = base_url.format(chapterID=id)
                
                retry = 1
                while retry < 10:
                    try:
                        response = requests.get(url=url, headers={"Authorization": f"Bearer {bearer_token}"})
                        if response.status_code == 401:
                            print('Error, status code == 401')
                            time.sleep(14)
                        break
                    except Exception as e:
                        print(f"Error during request: {e}")
                    retry +=1

                if response.status_code == 200 and response.text:
                    data = response.json()
                    base = data['baseUrl']
                    hash = data['chapter']['hash']
                    panels_list = data['chapter']['data']

                    for panel_num, panel in enumerate(panels_list):
                        type = panel.split('.')[-1]
                        final_name = base_file_name.format(manga_name=manga_name, language=language, chapter=chapter, panel=pad_number(str(panel_num)),type=type)
                        final_path = os.path.join(base_directory, final_name)
                        logging.info(f"Submitting download task for {manga_name}, Chapter: {chapter}, Panel: {panel_num} to executor")
                        future = executor.submit(save_to_local, base + "/data/" + hash + "/" + panel, final_path, bearer_token, refresh_token, client_id, client_secret)
                        futures.append(future)

                for future in futures:
                    future.result()
                futures.clear()

def save_to_local(url, file_path, bearer_token, refresh_token, client_id, client_secret):
    auto_refresh_token(refresh_token, client_id, client_secret)
    hardcoded_stop = 1
    while hardcoded_stop<=6:
        try:
            response = requests.get(url, headers={"Authorization": f"Bearer {bearer_token}"})

           
            if response.status_code == 200:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Create the directory if it does not exist
                with open(file_path, 'wb') as file:
                    file.write(response.content)
                    # print(f"Saved to {file_path}")
                
                break
            else:
                print(f"Failed to download file from {url}" + " " + str(response.status_code))
                time.sleep(2**hardcoded_stop)
        except:
            print("error in requests")
            time.sleep(2**hardcoded_stop)

        hardcoded_stop+=1

def upload_from_local_file(upload_name, local_file, bucket):
    # Function to upload to GCS from a local folder. Note each folder here represents 1 chapter and contains the panels for that chapter
    # We will use threading later on to upload multiple
    blob = bucket.blob(upload_name)
    blob.content_type = 'image/png'

    max_tries = 10
    start = 1
    while start < max_tries:
        try:
            blob.upload_from_filename(local_file)
            break
        except:
            time.sleep(2**start)
        start+=1

def upload_manga(bucket_name, manga_name):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    base_dir = "/Users/danfu/Downloads/"

    manga_dir = os.path.join(base_dir, manga_name)

    try:
        languages = [d for d in os.listdir(manga_dir) if d != ".DS_Store"]
    except FileNotFoundError:
        print(f"Directory {manga_dir} not found.")
        return

    for language in languages:
        language_dir = os.path.join(manga_dir, language)
        
        try:
            chapters = [c for c in os.listdir(language_dir) if c != ".DS_Store"]
        except FileNotFoundError:
            print(f"Directory {language_dir} not found.")
            continue

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []

            for chapter in chapters:
                chapter_dir = os.path.join(language_dir, chapter)
                panels = [p for p in os.listdir(chapter_dir) if p != ".DS_Store"]
                print(f"Starting upload for {manga_name} in {language}, chapter: {chapter}")
                for panel in panels:
                    local_file_path = os.path.join(chapter_dir, panel)
                    gcs_path = f"{manga_name}/{language}/{chapter}/{panel}"
      
                    future = executor.submit(upload_from_local_file, gcs_path, local_file_path, bucket)
                    futures.append(future)

            for future in futures:
                future.result()