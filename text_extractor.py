from PIL import Image
import pytesseract
import numpy as np
import cv2
from imutils.object_detection import non_max_suppression




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

def preprocess_image(img: Image):
    # Check if the image is grayscale; if not, convert to grayscale
    if img.ndim == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img

    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    return thresh


def preprocess_for_east_color(image_path):
    # Load the image in color
    image = cv2.imread(image_path)

    # Convert to LAB color space
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

    # Apply CLAHE to the L channel
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l, a, b = cv2.split(lab)
    l = clahe.apply(l)
    lab = cv2.merge([l, a, b])

    # Convert back to BGR color space
    processed_image = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    # Optionally apply mild blurring
    processed_image = cv2.GaussianBlur(processed_image, (3, 3), 0)

    return processed_image


def decode_predictions(scores,geometry):
    numRows, numCols = scores.shape[2:4]

    rects = []
    confidences = []


    for row in range(numRows):

        scoresData = scores[0, 0, row]
        yData0 = geometry[0, 0, row]
        xData1 = geometry[0, 1, row]
        yData2 = geometry[0, 2, row]
        xData3 = geometry[0, 3, row]
        anglesData = geometry[0, 4, row]

        for col in range(numCols):
          (offsetX, offsetY) = (col * 4.0, row * 4.0)

          if scoresData[col] > 0.4:
            height = yData0[col] + yData2[col]
            width = xData1[col] + xData3[col]
            angle = anglesData[col]
            cos = np.cos(angle)
            sin = np.sin(angle)

            endX = int(offsetX + (cos * xData1[col]) + (sin * yData2[col]))
            endY = int(offsetY - (sin * xData1[col]) + (cos * yData2[col]))
            startX = int(endX - width)
            startY = int(endY - height)
            rects.append((startX, startY, endX, endY))
            confidences.append(scoresData[col])

            

    return (rects,confidences)

def detect_text_regions(image_path: str):
    
    image = preprocess_for_east_color(image_path)
    orig = image.copy()

    # EAST requires images of a specific height and width
    (H, W) = image.shape[:2]
    # Your chosen dimensions (multiple of 32)
    newW = 320
    newH = 320
    rW = W / float(newW)
    rH = H / float(newH)

    # Resize the image and grab the new image dimensions
    image = cv2.resize(image, (newW, newH))
    (H, W) = image.shape[:2]

    # Load the pre-trained EAST text detector
    east_model_path = 'frozen_east_text_detection.pb'  
    net = cv2.dnn.readNet(east_model_path)

    # Construct a blob from the image
    blob = cv2.dnn.blobFromImage(image, 1.0, (W, H),(123.68, 116.78, 103.94), swapRB=True, crop=False)
    net.setInput(blob)
    (scores, geometry) = net.forward(["feature_fusion/Conv_7/Sigmoid", "feature_fusion/concat_3"])

    # Decode the predictions, then apply non-maxima suppression to suppress weak, overlapping bounding boxes
    # (Implement the decode_predictions function based on EAST model's output)
    rectangles, confidences = decode_predictions(scores, geometry)
    nms_threshold = 0.1  # Adjust as necessary
    boxes = non_max_suppression(np.array(rectangles), probs=confidences, overlapThresh = nms_threshold)

    text_regions = []
    for (startX, startY, endX, endY) in boxes:
        # Scale the bounding box coordinates based on the respective ratios
        startX = int(startX * rW)
        startY = int(startY * rH)
        endX = int(endX * rW)
        endY = int(endY * rH)

        # Extract the actual padded ROI
        text_regions.append(orig[startY:endY, startX:endX])

    
    # for i in range(len(text_regions)):
    #     text_regions[i] = preprocess_image(text_regions[i])
        

    return text_regions


