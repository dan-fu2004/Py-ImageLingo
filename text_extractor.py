from PIL import Image
import pytesseract
import numpy as np
import cv2


def load_image(image_path: str):
    # Load the image with PIL
    img = Image.open(image_path)

    # Convert the PIL image to a NumPy array
    img = np.array(img)

    # Check if the image has 3 channels (color image)
    if img.ndim == 3:
        # Convert RGB (PIL) to BGR (OpenCV)
        img = img[:, :, ::-1]

    return img


def extract_text(img: Image):
    text = pytesseract.image_to_string(img)
    return text


def preprocess_image(image_path):
 
    img = load_image(image_path)

    # Check if the image is grayscale; if not, convert to grayscale
    if img.ndim == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img

    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    return thresh


