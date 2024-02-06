from manga_download import *
from google.cloud import storage
import cv2
import numpy as np
import json


set_os_environ() #from manga_download

def collect_panels_annontations(manga_name, bucket_name = "manga_dataset_py_annotated"):
    path = f"{manga_name}/en/"
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=path)  
    image_paths = []
    text_boxes =[]

    for blob in blobs:
        text_boxes.append([])
        data = json.loads(blob.download_as_string(client=None))
        image_paths.append(data["task"]["data"]["image"].split("gs://")[1])

        for i in data["result"]:
            org_width = i["original_width"]
            org_height = i["original_height"]
            x = i["value"]["x"]/100 * org_width
            endx = i["value"]["width"]/100 * org_width
            y= i["value"]["y"]/100 * org_height
            endy= i["value"]["height"]/100 * org_height

            coord = (int(x), int(endx), int(y), int(endy))
            text_boxes[-1].append(coord)
        
    return image_paths, text_boxes

def load_image_from_gcs(image_path, bucket_name = "manga_dataset_py"):
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(image_path)
    image_data = blob.download_as_bytes()
    image_array = np.frombuffer(image_data, np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    return image

image, coord = collect_panels_annontations("ShinozakiMaintenance")

for index, value in enumerate(image):
     
    imagep = value.split("manga_dataset_py/")[-1]
    image = load_image_from_gcs(imagep)

    for j in coord[index]:
        cv2.rectangle(image, (j[0], j[2]), (j[0]+j[1], j[2]+j[3]), (0, 255, 0), 2)
    cv2.imshow("Boxes", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()