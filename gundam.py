import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QFileDialog, QVBoxLayout, QWidget, QScrollArea, QTextEdit, QMenuBar, QAction
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt

class OMRScanner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OMR Sheet Scanner")
        self.setGeometry(100, 100, 1200, 700)
        self.toolbar = self.addToolBar("Toolbar")
        self.menu_bar = self.menuBar()
        self.file_menu = self.menu_bar.addMenu("File")
        #self.zoom_in_menu = self.menu_bar.addMenu("Zoom_in")
        #self.zoom_out_menu = self.menu_bar.addMenu("Zoom_out")
        self.tools_menu = self.menu_bar.addMenu("Tools")

        import_action = QAction("Import Image", self)
        import_action.triggered.connect(self.load_image)
        self.file_menu.addAction(import_action)

        export_action = QAction("Export Coordinates", self)
        export_action.triggered.connect(self.export_coordinates)
        self.file_menu.addAction(export_action)

        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.triggered.connect(self.zoom_in)
        self.toolbar.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.triggered.connect(self.zoom_out)
        self.toolbar.addAction(zoom_out_action)

        #zoom_in_action = QAction("Zoom In", self)
        #zoom_in_action.triggered.connect(self.zoom_in)
        #self.zoom_in_menu.addAction(zoom_in_action)

        #zoom_out_action = QAction("Zoom Out", self)
        #zoom_out_action.triggered.connect(self.zoom_out)
        #self.zoom_out_menu.addAction(zoom_out_action)

        marker_action = QAction("Enable Marker", self)
        marker_action.triggered.connect(self.enable_marker)
        self.tools_menu.addAction(marker_action)

        self.scroll_area = QScrollArea(self)
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.scroll_area.setWidget(self.image_label)
        self.scroll_area.setWidgetResizable(True)

        self.coord_display = QTextEdit(self)
        self.coord_display.setReadOnly(True)
        self.coord_display.setFixedHeight(200)

        self.layout = QVBoxLayout()
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

        self.image_label.setMouseTracking(True)
        self.image_label.mouseMoveEvent = self.show_cursor_position
        self.image_label.mousePressEvent = self.mark_point

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open OMR Sheet", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.image = cv2.imread(file_path)
            self.display_image = self.image.copy()
            self.update_display()

    def update_display(self):
        if self.display_image is not None:
            # Scale the image for display based on the zoom factor
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

    def mark_point(self, event):
        if event.button() == Qt.LeftButton and self.image_label.pixmap() and self.marking_enabled:
            # Calculate coordinates relative to the original image
            label_width = self.image_label.width()
            label_height = self.image_label.height()
            pixmap_width = self.image_label.pixmap().width()
            pixmap_height = self.image_label.pixmap().height()

            # Calculate the offset due to scaling
            offset_x = max((label_width - pixmap_width) // 2, 0)
            offset_y = max((label_height - pixmap_height) // 2, 0)

            # Adjust the event position to account for the offset
            adjusted_x = event.pos().x() - offset_x
            adjusted_y = event.pos().y() - offset_y

            # Ensure the adjusted position is within the pixmap bounds
            if 0 <= adjusted_x < pixmap_width and 0 <= adjusted_y < pixmap_height:
                # Map the adjusted position to the original image coordinates
                x = int(adjusted_x / self.zoom_factor)
                y = int(adjusted_y / self.zoom_factor)

                # Ensure the coordinates are within the bounds of the original image
                if 0 <= x < self.image.shape[1] and 0 <= y < self.image.shape[0]:
                    self.coord_display.append(f"Marked: ({x}, {y})")
                    self.draw_marker(x, y)

                    if self.start_point is None:
                        self.start_point = (x, y)
                    else:
                        self.end_point = (x, y)
                        self.marking_enabled = False
                        self.mark_coordinates()

    def show_cursor_position(self, event):
        if self.image_label.pixmap() is None:
            # No image loaded, do nothing
            return

        label_width = self.image_label.width()
        label_height = self.image_label.height()
        pixmap_width = self.image_label.pixmap().width()
        pixmap_height = self.image_label.pixmap().height()

        # Calculate the offset due to scaling
        offset_x = max((label_width - pixmap_width) // 2, 0)
        offset_y = max((label_height - pixmap_height) // 2, 0)

        # Adjust the event position to account for the offset
        adjusted_x = event.pos().x() - offset_x
        adjusted_y = event.pos().y() - offset_y

        # Ensure the adjusted position is within the pixmap bounds
        if 0 <= adjusted_x < pixmap_width and 0 <= adjusted_y < pixmap_height:
            # Map the adjusted position to the original image coordinates
            x = int(adjusted_x / self.zoom_factor)
            y = int(adjusted_y / self.zoom_factor)

            # Display the cursor position in the status bar
            self.statusBar().showMessage(f"Cursor Position: ({x}, {y})")

    def draw_marker(self, x, y):
        # Draw the marker on the original image
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
