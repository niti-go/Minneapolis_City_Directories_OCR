# Extracting Records from Minneapolis City Directories

I developed a pipeline to extract structured resident data from scanned pages of the Minneapolis city directories (1900-1950), available via the [Hennepin County Library archive](https://box2.nmtvault.com/Hennepin2/). City directories list residents with their names, occupations, places of employment, spouses, and residences.

I demonstrate my pipeline on Pages 104-108 from the [1900 Minneapolis directory](https://box2.nmtvault.com/Hennepin2/jsp/RcWebImageViewer.jsp?doc_id=7083e412-1de2-42fe-b070-7f82e5c869a4/mnmhcl00/20130429/00000008&pg_seq=112&search_doc=). This involves training a model to detect layout of the pages and identify the regions containing resident listings, performing optical character recognition (OCR) on these sections, and structuring the results into json format.

<p align="center">
  <img src="https://github.com/user-attachments/assets/69645fd8-138f-484b-968e-7907fb2610c9" width="600"/>
</p>

## Why I built this project

This is a trial project for HouseNovel, a startup that creates interactive historical house timelines. I gained experience with OCR on scanned documents, layout detection by training object-detection models, data annotation with LabelStudio, and structuring messy data into clean JSON.

## How I Trained an Object Detection Model

We cannot perform OCR directly on the raw page images, because inconsistent multi-column formats and advertisements would result in nonsense. So, first, I needed to detect just the resident listing areas.

I labeled the resident records on 26 pages from the 1900 directory using LabelStudio: 20 for training, 6 for validation. I trained a YOLOv8n object detection model on my CPU (in under 15 minutes!). It reached 0.995 mAP@50, which is a metric for detection accuracy. You can find the final model weights in `train_yolo/runs/detect/train/weights/best.pt`. 

<p align="center">
<img width="250" alt="image" src="https://github.com/user-attachments/assets/417e708a-9d03-4d80-96d3-4723d1ee9eba" />
</p>

I used my trained model to detect resident listings on pages 104-108, and saved the cropped regions to `tesseract_ocr/cropped_records`. It is mostly accurate, except for some instances where the bounding box extends slightly beyond the resident listings. I am confident that the accuracy would be improved with more training data.

<p align="center">
<img width="450" alt="image" src="https://github.com/user-attachments/assets/264dd693-9c16-4b07-bd33-d58bf2d42f31" />
</p>

## Running Tesseract OCR on the Detected Regions
I applied Tesseract OCR to all the cropped images to extract the resident listings as text. I saved the results in both plain text format (`tesseract_ocr/ocr_results/combined_text.txt`) and JSON format, which contains metadata like word position.

Next steps: I'll inspect the plain text to understand OCR errors so I can decide how to clean them (like fixing obvious character mistakes). Then I can use named entity recognition (NER) to structure each record, word position data from the JSON to help separate individual records.

## What I've Learned So Far

- I first tried using LayoutParser’s existing NewspaperNavigator model to create bounding boxes around resident records, but it did not predict well. This is because it is not familiar with the city directory format. Fine-tuning models with LayoutParser is not straightforward (I tried following this [tutorial](https://www.youtube.com/watch?v=puOKTFXRyr4), but my training was stuck at the first iteration). So I switched to YOLO, which performs very well for the layout detection tasks we need.
- At first, I had also labeled advertisements in my training data and trained YOLO on two classes. However, since we only care about identifying records, I realized I could try removing those labels to simplify the data. I retrained the model, and its accuracy had improved.
- I used Cursor AI for the first time on this project, and am happy that it significantly sped up the time spent on it. It saved time with figuring out file path structures and model input/output formatting
- I used Cursor AI for the first time on this project, and it really helped speed things up. It was especially useful for handling file paths and making sure the model inputs and outputs were formatted correctly. I look forward to using it as a tool on future projects.

## If I had more time, I would:

- Train on more data (20 pages is very little), using my current model to auto-label in LabelStudio to make annotation faster
- Use a larger YOLO model if I have access to more computing resources
