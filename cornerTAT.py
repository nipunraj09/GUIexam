import cv2
import numpy as np

def detect_tat_ids(image_path, output_path):
    # Load image
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply adaptive thresholding
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 11, 2)
    
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter quadrilateral contours with width between 35 to 42 pixels
    quadrilateral_contours = []
    for cnt in contours:
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            if 28 <= w <= 35 and 28 <= h <= 35:
                quadrilateral_contours.append(approx)
    
    # Draw detected quadrilateral markers
    for cnt in quadrilateral_contours:
        cv2.drawContours(image, [cnt], -1, (0, 255, 0), 3)
    
    # Save output image
    cv2.imwrite(output_path, image)
    print(f"Processed image saved to {output_path}")

# Example usage
image_path = "200784.jpg"  # Replace with your input file path
output_path = "output_tat_ids.jpg"  # Replace with your desired output file path
detect_tat_ids(image_path, output_path)