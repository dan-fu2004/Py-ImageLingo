from text_extractor import *

preprocessed_image = preprocess_image("/Users/danfu/Downloads/Manga-Test.jpg")
print(extract_text(preprocessed_image))
# cv2.imshow('Preprocessed Image', preprocessed_image)
# cv2.waitKey(0)