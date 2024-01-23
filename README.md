# Py-ImageLingo
# Manga Translation Project

## Overview
This project aims to develop a machine learning model capable of detecting and extracting text from manga panels and using it automatically translate Manga. The model is designed to be robust across various manga styles and languages, providing a foundational tool for translation and localization efforts.
Note: This project is still a work in progress.

## Plan
This is a multistep project, automatically translating manga can be broken down in a few steps.
This is my plan: 
1. Use a computer vision model to detect text bubbles in a Manga panel
2. Send all detected regions of text to an Optical Character Recognition Engine
3. Get the translation from either DeepL or Chatgpt
4. Replace All text with new translated text

## Features
- Download High Quality Manga panels
- Text detection in manga images.
- Custom model trained on a diverse dataset of manga styles.

## Dataset
The dataset comprises several thousand annotated manga pages in various languages. The annotations include bounding box coordinates for text regions.
The dataset not currently public, all data is collected through MangaDex.org's API and all annontations will be done by yours truly.

## Dataset Preparation
- Data Annotation: Manga panels were annotated using tools like Label-Studio
- Data Preprocessing: Images were resized and normalized and converted to grayscale to fit the input requirements of the model.

## Updates and Current Status
Currently, I have finished up functions for retrieving and writing data, specifically, downloading and uploading manga panels to google cloud storage systems.
I am working on annotating my data and training my model.

## Acknowledgements
- Google's Tesseract Optical Character Recognition
- OpenCv and PIL Python Libraries
- MangaDex for collecting Data
- Label-Studio for Annotating Data.

---
