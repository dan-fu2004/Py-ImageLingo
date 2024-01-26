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

          if scoresData[col] > 0.6:
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

def resize_image_for_east(image):
    (h, w) = image.shape[:2]

    # Calculate the nearest multiple of 32 for both dimensions
    new_w = (w // 32) * 32
    new_h = (h // 32) * 32

    # If the dimension is already a multiple of 32, no need to resize
    if new_w == w and new_h == h:
        return image

    # Maintain aspect ratio
    ratio_w = new_w / w
    ratio_h = new_h / h
    ratio = min(ratio_w, ratio_h)

    # Compute new dimensions
    new_dim = (int(w * ratio), int(h * ratio))

    # Resize the image
    resized_image = cv2.resize(image, new_dim, interpolation=cv2.INTER_AREA)

    # Pad the resized image to reach the nearest multiple of 32
    delta_w = max(new_w - resized_image.shape[1], 0)
    delta_h = max(new_h - resized_image.shape[0], 0)
    top, bottom = delta_h // 2, delta_h - (delta_h // 2)
    left, right = delta_w // 2, delta_w - (delta_w // 2)

    color = [0, 0, 0]  # Black padding
    padded_image = cv2.copyMakeBorder(resized_image, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)

    return padded_image

def merge_boxes(boxes, threshold=10):
    # Sort the boxes by their starting x coordinate to improve the merging process
    boxes = [list(box) for box in boxes]
    boxes = sorted(boxes, key=lambda x: x[0])
    merged_boxes = []

    while boxes:
        # Take the first box
        base = boxes.pop(0)

        # This will contain all the boxes to merge with the current one
        to_merge = [base]

        # Compare it with the rest of the boxes
        for other in boxes:
            # If boxes are close enough (based on some threshold), consider them for merging
            if (abs(other[0] - base[2]) <= threshold and abs(other[1] - base[3]) <= threshold and
                abs(base[0] - other[2]) <= threshold and abs(base[1] - other[3]) <= threshold):
                to_merge.append(other)

        # Remove the boxes that will be merged
        boxes = [b for b in boxes if b not in to_merge]

        # Calculate the new bounding box coordinates
        min_startX = min([b[0] for b in to_merge])
        min_startY = min([b[1] for b in to_merge])
        max_endX = max([b[2] for b in to_merge])
        max_endY = max([b[3] for b in to_merge])

        # Add the new box to the merged_boxes
        merged_boxes.append([min_startX, min_startY, max_endX, max_endY])

    return merged_boxes

def detect_text_regions(image_path: str):
    
    image = cv2.imread(image_path)
    orig = image.copy()
    orig_annotated = image.copy()
    image = resize_image_for_east(image)

    # EAST requires images of a specific height and width
    (newH, newW) = image.shape[:2]
    (oldH, oldW) = orig.shape[:2]
    rW = oldW / float(newW)
    rH = oldH / float(newH)
    

    # Load the pre-trained EAST text detector
    east_model_path = 'frozen_east_text_detection.pb'  
    net = cv2.dnn.readNet(east_model_path)

    # Construct a blob from the image
    blob = cv2.dnn.blobFromImage(image, 1.0, (newW, newH),(123.68, 116.78, 103.94), swapRB=True, crop=False)
    net.setInput(blob)
    (scores, geometry) = net.forward(["feature_fusion/Conv_7/Sigmoid", "feature_fusion/concat_3"])

    # Decode the predictions, then apply non-maxima suppression to suppress weak, overlapping bounding boxes
    # (Implement the decode_predictions function based on EAST model's output)
    rectangles, confidences = decode_predictions(scores, geometry)
    nms_threshold = 0.1 # Adjust as necessary
    boxes = non_max_suppression(np.array(rectangles), probs=confidences, overlapThresh = nms_threshold)

    text_regions = []
    expansion = 5
    for (startX, startY, endX, endY) in boxes:
        # Scale the bounding box coordinates based on the respective ratios
        startX = int(startX * rW) - expansion
        startY = int(startY * rH) - expansion
        endX = int(endX * rW) + expansion
        endY = int(endY * rH) + expansion
        # Extract the actual padded ROI
        text_regions.append(orig[startY:endY, startX:endX])

    merged_boxes = merge_boxes(boxes, threshold=10)
    for startX, startY, endX, endY in merged_boxes:
        cv2.rectangle(orig_annotated, (startX, startY), (endX, endY), (0, 255, 0), 2)

    # for (box, score) in zip(boxes, confidences):
    #     # Scale the bounding box coordinates based on the respective ratios
    #     (startX, startY, endX, endY) = box
    #     startX = int(startX * rW)
    #     startY = int(startY * rH)
    #     endX = int(endX * rW)
    #     endY = int(endY * rH)

    #     # Put the probability text on the image
    #     text = "{:.4f}".format(score)
    #     cv2.putText(orig, text, (startX, startY - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Display the output image with probabilities
    cv2.imshow("Text Detection with Probabilities", orig_annotated)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    

    # for i in range(len(text_regions)):
    #     text_regions[i] = preprocess_image(text_regions[i])
        

    return merged_boxes


