from text_extractor import *

arr = detect_text_regions("/Users/danfu/Downloads/Test3.jpeg")

for i in arr:
    cv2.imshow('Preprocessed Image', i)
    cv2.waitKey(0)

