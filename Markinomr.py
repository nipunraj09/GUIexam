import cv2
import numpy as np
import pandas as pd
import os

def load_excel(file_path):
    return pd.read_excel(file_path)

def process_omr(image_dir, coordinates_file):
    coordinates = load_excel(coordinates_file)
    results = []
    output_file = os.path.join(image_dir, "OMR_Report.xlsx")
    
    for image_name in os.listdir(image_dir):
        if not image_name.lower().endswith(('.jpg', '.png', '.jpeg')):
            continue
        
        image_path = os.path.join(image_dir, image_name)
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            print(f"Failed to load image: {image_path}")
            continue
        
        threshold_img = cv2.threshold(image, 150, 255, cv2.THRESH_BINARY_INV)[1]
        image_results = []
        question_marks = {}
        
        for _, row in coordinates.iterrows():
            question, option, x, y = row['Question'], row['Option'], int(row['X']), int(row['Y'])
            region = threshold_img[max(0, y-10):y+10, max(0, x-10):x+10]
            
            if region.size == 0:
                print(f"Invalid region for question {question}, option {option} in {image_name}")
                continue
            
            fill_percentage = np.sum(region == 255) / region.size * 100
            marked_status = "Marked" if fill_percentage > 5 else "Unmarked"
            
            if marked_status == "Marked":
                if question not in question_marks:
                    question_marks[question] = []
                question_marks[question].append((option, fill_percentage))
            
            image_results.append([image_name, question, option, fill_percentage, marked_status, "No", "0%"])
        
        for row in image_results:
            image_name, question, option, fill_percentage, marked_status, _, _ = row
            if question in question_marks and len(question_marks[question]) > 1:
                row[5] = "Duplicate"
                row[6] = f"{max(opt[1] for opt in question_marks[question]):.2f}%"
        
        results.extend(image_results)
    
    df = pd.DataFrame(results, columns=["Image", "Question", "Option", "Fill %", "Status", "Duplicate Mark", "Duplicate Fill %"])
    df.to_excel(output_file, index=False)
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    image_directory = r"C:\Users\NIPUN\Desktop\18.03.2025\Images\01\0101" # Specify the directory containing images
    excel_file = r"C:\Users\NIPUN\Downloads\maredcordi.xlsx"  # Specify the path to the Excel file with coordinates
    
    process_omr(image_directory, excel_file)