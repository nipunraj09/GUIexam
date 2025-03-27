import cv2
import numpy as np
import pandas as pd
import os

def load_excel(file_path):
    return pd.read_excel(file_path)

def process_omr(root_dir, coordinates_file):
    coordinates = load_excel(coordinates_file)
    output_file = os.path.join(root_dir, "OMR_Report.xlsx")
    results = {}
    
    for subdir, _, files in os.walk(root_dir):
        for image_name in files:
            if not image_name.lower().endswith(('.jpg', '.png', '.jpeg')):
                continue
            
            image_path = os.path.join(subdir, image_name)
            image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if image is None:
                print(f"Failed to load image: {image_path}")
                continue
            
            threshold_img = cv2.threshold(image, 150, 255, cv2.THRESH_BINARY_INV)[1]
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
            
            if image_name not in results:
                results[image_name] = {}
            
            for question, options in question_marks.items():
                if len(options) > 1:
                    results[image_name][question] = f"Duplicate ({', '.join([f'{opt[0]}: {opt[1]:.2f}%' for opt in options])})"
                else:
                    results[image_name][question] = f"{options[0][0]}: {options[0][1]:.2f}%"
    
    df = pd.DataFrame.from_dict(results, orient='index').fillna("Unmarked")
    df.to_excel(output_file)
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    root_directory = r"C:\Users\NIPUN\Desktop\18.03.2025\Images\01"  # Specify the root directory containing all subfolders
    excel_file = r"C:\Users\NIPUN\Downloads\maredcordi.xlsx"  # Specify the path to the Excel file with coordinates
    
    process_omr(root_directory, excel_file)
