import os
import pytesseract
from PIL import Image
import json

# Paths
cropped_dir = "cropped_records"
ocr_results_dir = "ocr_results"
os.makedirs(ocr_results_dir, exist_ok=True)

#This script runs OCR on the cropped records
#It creates the folder ocr_results in the tesseract_ocr directory

#To run: % cd tesseract_ocr
#        % python run_ocr_on_crops.py

def save_as_json_files():
    """Save OCR results as individual JSON files and combine them"""
    json_dir = os.path.join(ocr_results_dir, "json_files")
    os.makedirs(json_dir, exist_ok=True)
    
    all_results = []
    
    for filename in os.listdir(cropped_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(cropped_dir, filename)
            
            # Perform OCR with detailed output
            ocr_data = pytesseract.image_to_data(Image.open(image_path), output_type=pytesseract.Output.DICT)
            
            # Extract text and confidence
            text = pytesseract.image_to_string(Image.open(image_path))
            
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
    output_file = 'ocr_results/combined_text_only.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(combined_text))

    print(f"Combined text saved to: {output_file}")
    print(f"Total files processed: {len(all_results)}")



if __name__ == "__main__":
    print("Starting OCR processing...")
    

    save_as_json_files()
    #convert_to_text()
    
    print("\nOCR processing complete!")