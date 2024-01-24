import os
from manga_collector import *

def download_manga_local(chapter_values, manga_name, client_id, client_secret, refresh_token, base_directory):
    global bearer_token
    base_url = "https://api.mangadex.org/at-home/server/{chapterID}"
    base_file_name = "{manga_name}/{language}/{chapter}/{panel}.{type}"


    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = []

        for language in chapter_values:
            for chapter, id in chapter_values[language]:
                print(f"Starting download for {manga_name} in {language}, chapter: {chapter}")
                auto_refresh_token(refresh_token, client_id, client_secret)
                url = base_url.format(chapterID=id)
                try:
                    response = requests.get(url=url, headers={"Authorization": f"Bearer {bearer_token}"})
                    if response.status_code == 401:
                        print('Error, status code == 401')
                        time.sleep(14)
                except Exception as e:
                    print(f"Error during request: {e}")

                if response.status_code == 200 and response.text:
                    data = response.json()
                    base = data['baseUrl']
                    hash = data['chapter']['hash']
                    panels_list = data['chapter']['data']

                for panel_num, panel in enumerate(panels_list):
                    type = panel.split('.')[-1]
                    final_name = base_file_name.format(manga_name=manga_name, language=language, chapter=chapter, panel=pad_number(str(panel_num)),type=type)
                    final_path = os.path.join(base_directory, final_name)
                    future = executor.submit(save_to_local, base + "/data/" + hash + "/" + panel, final_path, bearer_token, refresh_token, client_id, client_secret)
                    futures.append(future)

        for future in futures:
            future.result()

def save_to_local(url, file_path, bearer_token, refresh_token, client_id, client_secret):
    auto_refresh_token(refresh_token, client_id, client_secret)
    hardcoded_stop = 0
    while hardcoded_stop<=5:
        try:
            response = requests.get(url, headers={"Authorization": f"Bearer {bearer_token}"})

            hardcoded_stop+=1
            if response.status_code == 200:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Create the directory if it does not exist
                with open(file_path, 'wb') as file:
                    file.write(response.content)
            else:
                print(f"Failed to download file from {url}" + " " + str(response.status_code))
                time.sleep(7)
        except:
            time.sleep(6)