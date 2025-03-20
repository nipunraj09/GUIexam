import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QFileDialog, QVBoxLayout, QWidget, QPushButton, QScrollArea, QTextEdit
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt

class OMRScanner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OMR Sheet Scanner")
        self.setGeometry(100, 100, 1200, 700)

        self.scroll_area = QScrollArea(self)
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.scroll_area.setWidget(self.image_label)
        self.scroll_area.setWidgetResizable(True)

        self.marker_button = QPushButton("Mark Points", self)
        self.marker_button.clicked.connect(self.enable_marker)

        self.zoom_in_button = QPushButton("Zoom In", self)
        self.zoom_in_button.clicked.connect(self.zoom_in)
        
        self.zoom_out_button = QPushButton("Zoom Out", self)
        self.zoom_out_button.clicked.connect(self.zoom_out)
        
        self.export_button = QPushButton("Export Coordinates", self)
        self.export_button.clicked.connect(self.export_coordinates)
        
        self.coord_display = QTextEdit(self)
        self.coord_display.setReadOnly(True)
        self.coord_display.setFixedHeight(200)
        
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.marker_button)
        self.layout.addWidget(self.zoom_in_button)
        self.layout.addWidget(self.zoom_out_button)
        self.layout.addWidget(self.export_button)
        self.layout.addWidget(self.scroll_area)
        self.layout.addWidget(self.coord_display)

        self.container = QWidget()
        self.container.setLayout(self.layout)
        self.setCentralWidget(self.container)

        self.image = None
        self.display_image = None
        self.start_point = None
        self.end_point = None
        self.marking_enabled = False
        self.zoom_factor = 1.0
        self.coordinates = []
        
        self.num_questions = 25
        self.num_options = 4

        self.load_image()

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open OMR Sheet", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.image = cv2.imread(file_path)
            self.display_image = self.image.copy()
            self.update_display()

    def update_display(self):
        if self.display_image is not None:
            height, width, channel = self.display_image.shape
            bytes_per_line = 3 * width
            q_img = QImage(self.display_image.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            pixmap = QPixmap.fromImage(q_img)
            pixmap = pixmap.scaled(int(width * self.zoom_factor), int(height * self.zoom_factor), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(pixmap)

    def enable_marker(self):
        self.marking_enabled = True
        self.start_point = None
        self.end_point = None
        self.coordinates = []
        self.coord_display.clear()
        print("Marker enabled: Click two points on the image.")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.image_label.pixmap() and self.marking_enabled:
            x = int(event.pos().x() / self.zoom_factor) - self.image_label.x()
            y = int(event.pos().y() / self.zoom_factor) - self.image_label.y()
            
            if self.start_point is None:
                self.start_point = (x, y)
                self.draw_marker(x, y)
                print(f"Start point set at: {self.start_point}")
            else:
                self.end_point = (x, y)
                self.draw_marker(x, y)
                print(f"End point set at: {self.end_point}")
                self.marking_enabled = False
                self.mark_coordinates()

    def draw_marker(self, x, y):
        cv2.circle(self.display_image, (x, y), 5, (0, 0, 255), -1)
        self.update_display()

    def mark_coordinates(self):
        if self.start_point and self.end_point:
            x1, y1 = self.start_point
            x2, y2 = self.end_point

            row_step = (y2 - y1) / (self.num_questions - 1)
            col_step = (x2 - x1) / (self.num_options - 1)

            for q in range(self.num_questions):
                for opt in range(self.num_options):
                    x = int(x1 + opt * col_step)
                    y = int(y1 + q * row_step)
                    self.coordinates.append((q + 1, chr(65 + opt), x, y))
                    self.coord_display.append(f"Q{q+1}, {chr(65+opt)}: ({x}, {y})")
                    cv2.circle(self.display_image, (x, y), 5, (0, 0, 255), -1)

            self.update_display()
            print("Coordinates marked.")
    
    def zoom_in(self):
        self.zoom_factor *= 1.2
        self.update_display()
    
    def zoom_out(self):
        self.zoom_factor /= 1.2
        self.update_display()
    
    def export_coordinates(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Coordinates", "coordinates.csv", "CSV Files (*.csv)")
        if file_path:
            with open(file_path, "w") as f:
                f.write("Question,Option,X,Y\n")
                for coord in self.coordinates:
                    f.write(f"{coord[0]},{coord[1]},{coord[2]},{coord[3]}\n")
            print("Coordinates exported successfully.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OMRScanner()
    window.show()
    sys.exit(app.exec_())
