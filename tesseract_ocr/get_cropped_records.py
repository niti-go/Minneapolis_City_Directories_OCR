import os
import cv2
from PIL import Image
#After the yolo model has been trained and the predictions have been made on the test set (pages 104-108), 
#I use this script to crop the full pages down to the identified record sections
#Creates the folder cropped_records in the tesseract_ocr directory

#To run: % cd tesseract_ocr
#        % python get_cropped_records.py

print("Cropping pages down to record sections identified by yolo...")

# Paths
image_dir = "../data"
label_dir = "../train_yolo/runs/detect/predict/labels"
output_dir = "cropped_records"
os.makedirs(output_dir, exist_ok=True)

for label_file in os.listdir(label_dir):
    if not label_file.endswith('.txt'):
        continue
    # Find corresponding image to yolo's detections file
    # (try different extensions if needed)
    base_name = os.path.splitext(label_file)[0]
    for ext in ['.jpg', '.jpeg', '.png']:
        image_path = os.path.join(image_dir, base_name + ext)
        if os.path.exists(image_path):
            break
    else:
        print(f"No image found for {label_file}")
        continue

    img = cv2.imread(image_path)
    h, w = img.shape[:2] #h, w are the pixel dimensions of the image

    with open(os.path.join(label_dir, label_file), 'r') as f:
        lines = f.readlines()
        #read yolo's detections file

    for i, line in enumerate(lines):
        parts = line.strip().split()
        if len(parts) < 5:
            continue
        # YOLO format: class_id x_center y_center width height [confidence]
        class_id, x_center, y_center, box_w, box_h = map(float, parts[:5])
        # Get the 4 corners of the bounding box
        #First convert normalized values to pixel coordinates
        x_center, y_center, box_w, box_h = x_center * w, y_center * h, box_w * w, box_h * h
        x1 = int(x_center - box_w / 2)
        y1 = int(y_center - box_h / 2)
        x2 = int(x_center + box_w / 2)
        y2 = int(y_center + box_h / 2)
        # Ensure coordinates are within image bounds
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        
        # Add 10 pixels to the bottom of the bounding box
        #(Some images were otherwise slightly cut off)
        y2 = min(h, y2 + 10)
        
        # Crop and save
        crop = img[y1:y2, x1:x2]
        crop_filename = f"{base_name}_crop_{i}.png"
        output_path = os.path.join(output_dir, crop_filename)

        # Ensure image is saved at 300 DPI
        crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(crop_rgb)
        pil_image.save(output_path, dpi=(300, 300))
        print(f"Saved {crop_filename} at 300 DPI")

print("Cropping full pages down to record sections is complete!")
print("Saved cropped records in the cropped_records folder")