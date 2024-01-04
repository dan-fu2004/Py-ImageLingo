from PIL import Image
import pytesseract
import numpy as np
import cv2


def load_image(file_path: str) -> Image:
    img = np.array(Image.open(file_path))
    return img



def extract_text(img: Image) -> str:
    text = pytesseract.image_to_string(img)
    return text


def preprocess_image(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    return thresh



preprocessed_image = preprocess_image("/Users/danfu/Downloads/Manga-Test.jpg")
cv2.imshow('Preprocessed Image', preprocessed_image)
cv2.waitKey(0)