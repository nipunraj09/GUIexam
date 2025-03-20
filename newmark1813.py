import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QFileDialog, QVBoxLayout, QWidget, QScrollArea, QTextEdit, QMenuBar, QAction, QInputDialog, QTableWidget, QTableWidgetItem, QMessageBox, QSplitter, QMenu, QStatusBar, QPushButton
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt

class OMRScanner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OMR Sheet Scanner")
        self.setGeometry(100, 100, 1200, 700)

        # Initialize group management attributes
        self.groups = {}  # Dictionary to store groups and their coordinates
        self.current_group = None
        self.last_question_number = 0  # Tracks the last question number across groups

        # Create menus and toolbar
        self.toolbar = self.addToolBar("Toolbar")
        self.menu_bar = self.menuBar()
        self.file_menu = self.menu_bar.addMenu("File")
        self.tools_menu = self.menu_bar.addMenu("Tools")
        self.response_menu = self.menu_bar.addMenu("Response Type")  # Dropdown for response types
        self.group_menu = self.menu_bar.addMenu("Group")  # Dropdown for groups

        # Add file menu options
        load_image_action = QAction("Load Image", self)
        load_image_action.triggered.connect(self.load_image)
        self.file_menu.addAction(load_image_action)

        export_coordinates_action = QAction("Export Coordinates", self)
        export_coordinates_action.triggered.connect(self.export_coordinates)
        self.file_menu.addAction(export_coordinates_action)

        # Add response type options
        self.response_with_rows_action = QAction("Responses with Rows", self)
        self.response_with_rows_action.triggered.connect(self.set_response_with_rows)
        self.response_menu.addAction(self.response_with_rows_action)

        self.response_with_cols_action = QAction("Responses with Columns", self)
        self.response_with_cols_action.triggered.connect(self.set_response_with_cols)
        self.response_menu.addAction(self.response_with_cols_action)

        self.response_with_rows_cols_action = QAction("Responses with Rows and Columns", self)
        self.response_with_rows_cols_action.triggered.connect(self.set_response_with_rows_cols)
        self.response_menu.addAction(self.response_with_rows_cols_action)

        # Add group management options
        self.update_group_menu()  # Ensure this is called after initializing self.groups
        delete_group_action = QAction("Delete Current Group", self)
        delete_group_action.triggered.connect(self.delete_group)
        self.group_menu.addAction(delete_group_action)

        # Add marker options to the toolbox and toolbar
        enable_marker_action = QAction("Enable Marker", self)
        enable_marker_action.triggered.connect(self.enable_marker)
        self.tools_menu.addAction(enable_marker_action)  # Add to Tools menu
        self.toolbar.addAction(enable_marker_action)     # Add to Toolbar

        disable_marker_action = QAction("Disable Marker", self)
        disable_marker_action.triggered.connect(self.disable_marker)
        self.tools_menu.addAction(disable_marker_action)  # Add to Tools menu
        self.toolbar.addAction(disable_marker_action)     # Add to Toolbar

        clear_coordinates_action = QAction("Clear Marked Coordinates", self)
        clear_coordinates_action.triggered.connect(self.clear_marked_coordinates)
        self.tools_menu.addAction(clear_coordinates_action)

        detect_quadrilaterals_action = QAction("Detect Quadrilaterals", self)
        detect_quadrilaterals_action.triggered.connect(self.detect_quadrilaterals)
        self.tools_menu.addAction(detect_quadrilaterals_action)

        # Add zoom options to the toolbox
        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.triggered.connect(self.zoom_in)
        self.tools_menu.addAction(zoom_in_action)
        self.toolbar.addAction(zoom_in_action)  # Add to Toolbar

        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.triggered.connect(self.zoom_out)
        self.tools_menu.addAction(zoom_out_action)
        self.toolbar.addAction(zoom_out_action)  # Add to Toolbar

        # Add status bar with delete button aligned to the right
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Cursor Position: (0, 0)")
        self.delete_group_button = QPushButton("Delete Current Group")
        self.delete_group_button.clicked.connect(self.delete_group)
        self.status_bar.addPermanentWidget(self.delete_group_button)  # Align to the right

        # Scroll area for the image
        self.scroll_area = QScrollArea(self)
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.scroll_area.setWidget(self.image_label)
        self.scroll_area.setWidgetResizable(True)

        # Coordinate display
        self.coord_display = QTextEdit(self)
        self.coord_display.setReadOnly(True)

        # Table to display coordinates
        self.coord_table = QTableWidget(self)
        self.coord_table.setColumnCount(3)
        self.coord_table.setHorizontalHeaderLabels(["Question", "Options", "Coordinates"])

        # Use a splitter to allow resizing
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.addWidget(self.scroll_area)
        self.splitter.addWidget(self.coord_display)
        self.splitter.addWidget(self.coord_table)

        self.container = QWidget()
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.splitter)
        self.container.setLayout(self.layout)
        self.setCentralWidget(self.container)

        self.image = None
        self.display_image = None
        self.start_point = None
        self.end_point = None
        self.marking_enabled = False
        self.zoom_factor = 1.0

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

    def disable_marker(self):
        """Disable the marker."""
        self.marking_enabled = False
        print("Marker disabled.")

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

            if self.num_questions > 1 and self.num_options > 1:  # For rows and columns
                self.mark_coordinates_rows_and_columns()
            elif self.num_options > 1:  # Single question with multiple responses
                self.mark_coordinates_rows_or_columns()
            else:
                QMessageBox.warning(self, "Invalid Input", "Please specify both rows and columns.")

            self.update_display()
            self.update_coord_table()
            QMessageBox.information(self, "Coordinates Saved", f"Coordinates saved for '{self.current_group}'.")

    def mark_coordinates_rows_or_columns(self):
        """Mark coordinates for a single question with multiple responses in a row or column."""
        if self.start_point and self.end_point:
            x1, y1 = self.start_point
            x2, y2 = self.end_point

            if self.num_options > 1:  # Single question with multiple responses
                if y1 == y2:  # Responses with Rows (horizontal)
                    x_step = (x2 - x1) / (self.num_options - 1)  # Change in x-axis
                    y_step = 0  # y-axis remains constant
                elif x1 == x2:  # Responses with Columns (vertical)
                    x_step = 0  # x-axis remains constant
                    y_step = (y2 - y1) / (self.num_options - 1)  # Change in y-axis
                else:
                    QMessageBox.warning(self, "Invalid Input", "For rows, y-coordinates must be the same. For columns, x-coordinates must be the same.")
                    return

                # Generate coordinates for a single question with multiple responses
                question_number = self.last_question_number + 1
                for opt in range(self.num_options):
                    x = int(x1 + opt * x_step)
                    y = int(y1 + opt * y_step)
                    self.groups[self.current_group].append((question_number, chr(65 + opt), x, y))
                    self.coord_display.append(f"Q{question_number}, {chr(65+opt)}: ({x}, {y})")
                    cv2.circle(self.display_image, (x, y), 5, (0, 0, 255), -1)

                self.last_question_number += 1  # Increment question number for the next group
            else:
                QMessageBox.warning(self, "Invalid Input", "Please specify multiple responses.")

            self.update_display()
            self.update_coord_table()
            QMessageBox.information(self, "Coordinates Saved", f"Coordinates saved for '{self.current_group}'.")

    def mark_coordinates_rows_and_columns(self):
        """Mark coordinates for multiple questions and responses in a grid."""
        if self.start_point and self.end_point:
            x1, y1 = self.start_point
            x2, y2 = self.end_point

            if self.num_questions > 1 and self.num_options > 1:  # For rows and columns
                x_step = (x2 - x1) / (self.num_options - 1)  # Change in x-axis for columns
                y_step = (y2 - y1) / (self.num_questions - 1)  # Change in y-axis for rows

                # Generate coordinates for a grid of questions and responses
                for q in range(self.num_questions):
                    for opt in range(self.num_options):
                        x = int(x1 + opt * x_step)
                        y = int(y1 + q * y_step)
                        question_number = self.last_question_number + q + 1
                        self.groups[self.current_group].append((question_number, chr(65 + opt), x, y))
                        self.coord_display.append(f"Q{question_number}, {chr(65+opt)}: ({x}, {y})")
                        cv2.circle(self.display_image, (x, y), 5, (0, 0, 255), -1)

                self.last_question_number += self.num_questions  # Increment question numbers for the next group
            else:
                QMessageBox.warning(self, "Invalid Input", "Please specify both rows and columns.")

            self.update_display()
            self.update_coord_table()
            QMessageBox.information(self, "Coordinates Saved", f"Coordinates saved for '{self.current_group}'.")

    def set_response_with_rows_cols(self):
        # Prompt user for number of questions and responses in one dialog
        input_dialog = QInputDialog(self)
        input_dialog.setWindowTitle("Rows and Columns")
        input_dialog.setLabelText("Enter number of questions (rows) and responses (columns) separated by a comma (e.g., 5,4):")
        input_dialog.setTextValue("5,4")
        if input_dialog.exec_() == QInputDialog.Accepted:
            try:
                num_questions, num_responses = map(int, input_dialog.textValue().split(","))
                self.num_questions = num_questions  # Set the number of questions (rows)
                self.num_options = num_responses  # Set the number of responses (columns)
                self.current_group = f"Group {len(self.groups) + 1}"
                self.groups[self.current_group] = []
                self.update_group_menu()
                QMessageBox.information(self, "Group Created", f"Group '{self.current_group}' created. Mark initial and final coordinates.")
            except ValueError:
                QMessageBox.warning(self, "Invalid Input", "Please enter valid numbers separated by a comma.")

    def set_response_with_rows(self):
        # Prompt user for number of responses
        num_responses, ok = QInputDialog.getInt(self, "Responses with Rows", "Enter number of responses:", 4, 2, 100)
        if ok:
            self.num_options = num_responses  # Set the number of responses
            self.num_questions = 1  # Single question
            self.current_group = f"Group {len(self.groups) + 1}"
            self.groups[self.current_group] = []
            self.update_group_menu()
            QMessageBox.information(self, "Group Created", f"Group '{self.current_group}' created. Mark initial and final coordinates.")

    def set_response_with_cols(self):
        # Prompt user for number of responses
        num_responses, ok = QInputDialog.getInt(self, "Responses with Columns", "Enter number of responses:", 4, 2, 100)
        if ok:
            self.num_options = num_responses  # Set the number of responses
            self.num_questions = 1  # Single question
            self.current_group = f"Group {len(self.groups) + 1}"
            self.groups[self.current_group] = []
            self.update_group_menu()
            QMessageBox.information(self, "Group Created", f"Group '{self.current_group}' created. Mark initial and final coordinates.")

    def view_groups(self):
        # Display a list of groups
        if not self.groups:
            QMessageBox.information(self, "No Groups", "No groups have been created yet.")
            return
        group_list = "\n".join(self.groups.keys())
        QMessageBox.information(self, "Groups", f"Available Groups:\n{group_list}")

    def delete_group(self):
        """Delete the current group and clear its marks."""
        if self.current_group and self.current_group in self.groups:
            del self.groups[self.current_group]
            self.current_group = None
            self.coord_table.setRowCount(0)
            self.display_image = self.image.copy()  # Clear marks from the image
            self.update_display()
            self.update_group_menu()
            QMessageBox.information(self, "Group Deleted", "The current group has been deleted.")
        else:
            QMessageBox.warning(self, "No Group Selected", "No group is currently selected.")

    def clear_marked_coordinates(self):
        # Clear all marked coordinates from the display
        self.display_image = self.image.copy()
        self.update_display()
        QMessageBox.information(self, "Cleared", "All marked coordinates have been cleared.")

    def zoom_in(self):
        self.zoom_factor *= 1.2
        self.update_display()
    
    def zoom_out(self):
        self.zoom_factor /= 1.2
        self.update_display()
    
    def export_coordinates(self):
        # Export all group coordinates to a CSV file
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Coordinates", "coordinates.csv", "CSV Files (*.csv)")
        if file_path:
            with open(file_path, "w") as f:
                f.write("Group,Question,Option,X,Y\n")
                for group_name, coords in self.groups.items():
                    for coord in coords:
                        f.write(f"{group_name},{coord[0]},{coord[1]},{coord[2]},{coord[3]}\n")
            QMessageBox.information(self, "Export Successful", "Coordinates exported successfully.")

    def update_group_menu(self):
        # Clear existing group menu items
        self.group_menu.clear()

        # Add groups to the dropdown menu
        for group_name in self.groups.keys():
            group_action = QAction(group_name, self)
            group_action.triggered.connect(lambda checked, g=group_name: self.view_group(g))
            self.group_menu.addAction(group_action)

    def view_group(self, group_name):
        # Display the coordinates of the selected group in the coord_table
        self.current_group = group_name
        self.update_coord_table()

    def detect_quadrilaterals(self):
        if self.image is None:
            QMessageBox.warning(self, "No Image", "Please load an image first.")
            return

        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
            if len(approx) == 4:  # Quadrilateral
                x, y, w, h = cv2.boundingRect(approx)
                if 35 <= w <= 40 and 35 <= h <= 40:  # Check size range
                    cv2.drawContours(self.display_image, [approx], -1, (0, 255, 0), 2)

        self.update_display()
        QMessageBox.information(self, "Detection Complete", "Quadrilaterals detected and highlighted.")

    def update_coord_table(self):
        """Update the coordinate table with the current group's coordinates."""
        if self.current_group and self.current_group in self.groups:
            grouped_data = {}
            for coord in self.groups[self.current_group]:
                question = coord[0]
                option = coord[1]
                coordinate = f"({coord[2]}, {coord[3]})"
                if question not in grouped_data:
                    grouped_data[question] = {"options": [], "coordinates": []}
                grouped_data[question]["options"].append(option)
                grouped_data[question]["coordinates"].append(coordinate)

            self.coord_table.setRowCount(len(grouped_data))
            for row, (question, data) in enumerate(grouped_data.items()):
                options = ", ".join(data["options"])
                coordinates = ", ".join(data["coordinates"])
                self.coord_table.setItem(row, 0, QTableWidgetItem(str(question)))  # Question
                self.coord_table.setItem(row, 1, QTableWidgetItem(options))       # Options
                self.coord_table.setItem(row, 2, QTableWidgetItem(coordinates))   # Coordinates

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OMRScanner()
    window.show()
    sys.exit(app.exec_())
