import os
import pytesseract
from PIL import Image
import json
import cv2
import numpy as np

# Paths
cropped_dir = "cropped_records"
ocr_results_dir = "ocr_results"
os.makedirs(ocr_results_dir, exist_ok=True)

#This script runs OCR on the cropped records
#It creates the folder ocr_results in the tesseract_ocr directory

#To run: % cd tesseract_ocr
#        % python run_ocr_on_crops.py

def preprocess_image(image_path):
    """Preprocess image to improve OCR accuracy"""
    # Read image
    img = cv2.imread(image_path)
    
    
    # Convert to grayscale
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    kernel = np.ones((1, 1), np.uint8)
    img = cv2.dilate(img, kernel, iterations=1)
    img = cv2.erode(img, kernel, iterations=1)
    
    img = cv2.threshold(cv2.medianBlur(img, 3), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    
   
    
    
    ditto_mark = cv2.imread("ditto_character.png", 0)
    
    result = cv2.matchTemplate(img, ditto_mark, cv2.TM_CCOEFF_NORMED)
    threshold = 0.8
    locations = np.where(result >= threshold)
    h, w = ditto_mark.shape
    
    # Draw rectangles
    for pt in zip(*locations[::-1]):  # (x, y)
        top_left = pt
        bottom_right = (pt[0] + w, pt[1] + h)
        cv2.rectangle(img, top_left, bottom_right, (0, 0, 255), 2)
        print(f"Ditto mark detected at y={pt[1]}")
    
     # Save processed image to imgs_processed folder inside ocr_results
    processed_dir = os.path.join(ocr_results_dir, "imgs_processed")
    os.makedirs(processed_dir, exist_ok=True)
    filename = os.path.basename(image_path)
    processed_path = os.path.join(processed_dir, filename)
    cv2.imwrite(processed_path, img)
    
    return img

# def preprocess_image(image_path):
#     """Preprocess image to preserve fine details like ditto marks"""
#     # Read and convert to grayscale
#     img = cv2.imread(image_path)
#     gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
#     # Upscale image to help OCR detect small marks
#     scale_factor = 2
#     gray = cv2.resize(gray, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)
    
#     # Apply bilateral filter to denoise while preserving edges
#     filtered = cv2.bilateralFilter(gray, 9, 75, 75)
    
#     # Adaptive threshold to keep local contrast (helps ditto marks)
#     thresh = cv2.adaptiveThreshold(
#         filtered, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
#         cv2.THRESH_BINARY, 11, 2
#     )

#     return thresh

def save_as_json_files():
    """Save OCR results as individual JSON files and combine them"""
    json_dir = os.path.join(ocr_results_dir, "json_files")
    os.makedirs(json_dir, exist_ok=True)
    
    all_results = []
    
    for filename in os.listdir(cropped_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(cropped_dir, filename)
            
            # Preprocess the image
            preprocessed_img = preprocess_image(image_path)
            
            # Convert back to PIL Image for pytesseract
            pil_img = Image.fromarray(preprocessed_img)
            
            #print("""--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,()"'-½""")
            
            # Configure Tesseract page segmentation mode = 6 -> "uniform block of text"
            # And prevent incorrectly detecting characters like :, $, *, that are not in city directories
            #custom_config = '--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,()-½\\"'
            custom_config = ( 
            '--oem 3 --psm 6 '
            '-c "tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.-,()½ \\"" '
            '-c user_words=./user-words '
            )
            #custom_config = "--oem 3 --psm 6"

            
            # Perform OCR with detailed output
            ocr_data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT, config=custom_config)
            
            # Extract text and confidence
            text = pytesseract.image_to_string(pil_img, config=custom_config)
            
            # Create result for this image
            result = {
                "filename": filename,
                "text": text.strip(),
                #"confidence": ocr_data.get('conf', []),
                "word_count": len(text.split()),
                "ocr_data": ocr_data  # Full OCR data if needed
            }
            
            # Save individual JSON file
            json_filename = filename.rsplit('.', 1)[0] + '.json'
            json_path = os.path.join(json_dir, json_filename)
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            all_results.append(result)
            print(f"OCR completed for {filename} -> {json_filename}")
    
    # Save combined JSON file
    combined_path = os.path.join(ocr_results_dir, "all_ocr_results.json")
    with open(combined_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\nCombined results saved to: {combined_path}")
    print(f"Total images processed: {len(all_results)}")

def convert_to_text():
    """Convert OCR results to a combined text file: combined_text_only.txt"""
    # Read the combined OCR results
    with open('ocr_results/all_ocr_results.json', 'r', encoding='utf-8') as f:
        all_results = json.load(f)

    # Extract all text and combine
    combined_text = []
    for result in all_results:
        filename = result['filename']
        text = result['text']
        
        # Add filename as header and the text
        combined_text.append(f"=== {filename} ===\n{text}\n")

    # Save to a new file
    output_file = 'ocr_results/combined_text_only2.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(combined_text))

    print(f"Combined text saved to: {output_file}")
    print(f"Total files processed: {len(all_results)}")



if __name__ == "__main__":
    print("Starting OCR processing...")
    

    save_as_json_files()
    convert_to_text()
    
    print("\nOCR processing complete!")