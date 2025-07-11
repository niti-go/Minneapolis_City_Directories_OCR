# Extracting Records from Minneapolis City Directories

I am developing a pipeline to extract structured resident data from scanned pages of the Minneapolis city directories (1900-1950), available via the [Hennepin County Library archive](https://box2.nmtvault.com/Hennepin2/). City directories list residents with their names, occupations, places of employment, spouses, and residences.

I tested my process on Pages 104-108 from the [1900 Minneapolis directory](https://box2.nmtvault.com/Hennepin2/jsp/RcWebImageViewer.jsp?doc_id=7083e412-1de2-42fe-b070-7f82e5c869a4/mnmhcl00/20130429/00000008&pg_seq=112&search_doc=). This involves training a model to detect the parts of the page that list resident information, running optical character recognition (OCR) on these sections, and structuring the results as JSON.

<p align="center">
  <img src="https://github.com/user-attachments/assets/69645fd8-138f-484b-968e-7907fb2610c9" width="600"/>
<br>
  <em>My process to structure Minneapolis 1900 city directory data.</em>
</p>

## Why I built this project

This is a trial project. I learned a lot about image processing and improving OCR results, layout detection by training object-detection models, data annotation with LabelStudio, and structuring messy data.

# Phase One: OCR + Structured Data Extraction
## How I Trained an Object Detection Model

We cannot perform OCR directly on the raw page images, because inconsistent multi-column formats and advertisements would result in nonsense. So, first, I needed to detect just the resident listing areas.

I labeled the resident records on 26 pages from the 1900 directory using LabelStudio: 20 for training, 6 for validation. I trained a YOLOv8n object detection model on my CPU (in under 15 minutes!). It reached 0.995 mAP@50, which is a metric for detection accuracy. You can find the final model weights in `train_yolo/runs/detect/train/weights/best.pt`. 

<p align="center">
<img width="250" alt="image" src="https://github.com/user-attachments/assets/417e708a-9d03-4d80-96d3-4723d1ee9eba" />
  <br>
  <em>A page I annotated for the training data.</em>
</p>

I used my trained model to detect the resident listings from unseen pages 104-108, and saved the cropped sections to `tesseract_ocr/cropped_records`. It is mostly accurate, except for one case where the bounding box extends slightly too far. I am confident that with more training data, the accuracy would improve.

<p align="center">
<img width="450" alt="image" src="https://github.com/user-attachments/assets/264dd693-9c16-4b07-bd33-d58bf2d42f31" />
<br>
<em>The trained model detecting resident listings on pages 104 and 105.</em>
</p>

## Running Tesseract OCR on the Detected Regions
I applied Tesseract OCR to the cropped images to extract the resident listings as text. I saved the results in two formats: plain text (`tesseract_ocr/ocr_results/combined_text.txt`) and JSON, which includes extra metadata like word position.

At first, using Tesseract with default settings gave very messy results. Then I realized the importance of image preprocessing and OCR configurations. These helped greatly improve the quality of OCR output.

<table align="center">
  <tr>
    <td><pre>"os musa pete r (wid oe H), vr 3107 2d
Bltzabeth Wi "</pre></td>
    <td><pre>---></pre></td>
    <td><pre>"Blizabeth J (wid Andrew H), r 3107 2d
av 8."</pre></td>
  </tr>
</table>
<p align="center">
<em>Improvement in OCR output.</em>
</p>

**Some tricks I discovered:**

- Image filtering techniques like median blurring can reduce noise from the image, so random dots and smudges don't confuse the OCR tool.
- Since I knew the directories only contain regular letters, numbers, and common punctuation (like periods or commas), I gave Tesseract a whitelist of allowed characters. This stops it from trying to read odd symbols like © or ¢ that don’t belong in the text.
- Saving images in `.png` format with a resolution of 300 DPI is ideal clarity for Tesseract.
- Tesseract has different modes for how it scans a page. By default, it tries to detect  blocks of text on its own, which wasn’t necessary here since I had already cropped down to just the records. So, I switched to a mode that treats everything as a single block of uniform text (called Page Segmentation Mode 6). I also tested Mode 4, which assumes rows of text are connected, since records are formatted in rows for the most part.

## Challenges Faced
Tesseract was rarely able to identify ditto marks (") at the beginning of a record, which is very important to tell us that an individual's last name is connected to a previous record.

I initially thought the denoising steps might be causing the ditto marks to disappear, but after inspecting the post-processed images, they are still very clear. I think it's caused by Tesseract's internal logic that removing whitespace in the beginnings of lines.

However, training a separate object-detection model to recognize ditto marks worked very well.

<p align="center">
<img width="250" alt="image" src="https://github.com/user-attachments/assets/afac0c8f-31ab-46b3-996a-88157c2cbc8e" />
  <br>
  <em>A separate OpenCV model is able to identify ditto marks.</em>
</p>

An idea I have is to separately identify which lines contain ditto marks using the new model, and correspondingly insert them into the post-OCR'd text based on their y-position.

## Next Steps
Due to time constraints, I still need to finish the following tasks:

Once the OCR text is more accurate by inserting ditto marks, we need to distinguish between individual records, which can be one or multiple lines long.

<table align="center">
  <tr>
    <td><pre>Belle W (wid George), b 2430 lith av s.
Charles, tinner F T Thompson, r 2422
Central av.
David, mach opr H C Akeley Lbr Co,
r 605. 2lst av n.
Brick, tmstr, r 827 29th av s.
Frank, lab, rms 204 Hennepin. av.</pre></td>
    <td><pre>---></pre></td>
    <td><pre>Belle W (wid George), b 2430 lith av s.<hr>Charles, tinner F T Thompson, r 2422
Central av.<hr>David, mach opr H C Akeley Lbr Co,
r 605. 2lst av n.<hr>Brick, tmstr, r 827 29th av s.<hr>Frank, lab, rms 204 Hennepin. av.</pre></td>
  </tr>
</table>
<p align="center">
<em>Separating text into individual records.</em>
</p>

I noticed that indented lines on the scanned page are typically a continuation of the record on the previous line, while non-indented lines mark the beginning of a new entry. Since I have the JSON output, which also contains word position, I would modify the text file to indicate whether each line is indented or not. 

To identify the indents, I would create a data point for each first word in a line. I would run a means-clustering algorithm with 2 means on the x-position of the points. Since all lines start with either an indent or not, one mean would be the x-position of indented lines, and one mean would be the x-position of non-indented lines.

Also, I can use the fact that lines starting with a lowercase are usually a continutation of the previous line.

Next, I would need to identify different fields within a record. Commas can help in separating some fields, and I can use NER to improve confidence in the the name and spouse fields. Addresses are usually numbers and end in an abbreviation like "av" or "s". Also, a page in the 1900 directory contains a dictionary of abbreviations (e.g. "b" = "boards", "smstrs" = "seamstress"), which can help with identifying occupation and residence type. If the line contains a ditto mark, the last name is copied from the previous record. 

# Phase Two: Real World Application - 1807 Dupont Ave S
The goal is to create a timeline of past residents between 1902 and 1950 at 1807 Dupont Ave S, Minneapolis, MN 55403.

After following the steps above, each year from 1900 to 1950 would contain JSON data of residents. From [Zillow](https://www.zillow.com/homedetails/1807-Dupont-Ave-S-Minneapolis-MN-55403/1951320_zpid), we see that the home was built in 1902, so we can start from 1902 and iterate over each year, searching for records where the address matches and keeping track of the names of any people who live there. If the name is the same over multiple years, I would record in the timeline that that person lived there for those years.

It's possible that names change slightly in the data from year to year, for example, from spouse changes or OCR errors. If most other fields match, then we can assume it's the same person living in the home.

## Additional Notes

- I first tried using LayoutParser’s existing NewspaperNavigator model to create bounding boxes around resident records, but it did not predict well. This is because it is not familiar with the city directory format. Fine-tuning models with LayoutParser is not straightforward (I tried following this [tutorial](https://www.youtube.com/watch?v=puOKTFXRyr4), but my training was stuck at the first iteration). So, I switched to YOLO, which integrates easier with my annotated data and performs very well for the layout detection tasks we need.
- At first, I had also labeled advertisements in my training data and trained YOLO on two classes. However, since we only care about identifying records, I realized I could remove those labels to simplify the data. I retrained the model, and the accuracy improved.
- I used Cursor AI for the first time on this project, and it really helped speed things up. It was especially useful for handling file paths and making sure the model inputs and outputs were formatted correctly. I look forward to using it as a tool on future projects (validating its output with other sources, of course).

## If I had more time, I would:

- Train the layout detection model on more data (20 pages is very little), using my current model to auto-label in LabelStudio to make annotation faster
- Improve OCR accuracy even more by experimenting with more image processing techniques
- Search for other databases online that would be helpful in cross-referencing the accuracy of our data
