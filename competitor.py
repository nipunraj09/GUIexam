import tkinter as tk
from tkinter import messagebox
import pandas as pd
from tkinter import filedialog

# Create an empty DataFrame to store the data
data = pd.DataFrame(columns=["Competitor Name", "Exam Name", "Year", "Exam Value"])

# Function to append data to the DataFrame
def add_to_df():
    global data
    competitor_name = competitor_name_entry.get()
    exam_name = exam_name_entry.get()
    year = year_entry.get()
    exam_value = exam_value_entry.get()
    
    if not competitor_name or not exam_name or not year or not exam_value:
        messagebox.showerror("Input Error", "All fields are required!")
        return
    
    # Append the new row to the DataFrame
    try:
        year = int(year)
        data = pd.concat([data, pd.DataFrame({"Competitor Name": [competitor_name], 
                                              "Exam Name": [exam_name], 
                                              "Year": [year], 
                                              "Exam Value": [exam_value]})], 
                         ignore_index=True)
        messagebox.showinfo("Success", "Data added successfully!")
        # Clear the input fields
        competitor_name_entry.delete(0, tk.END)
        exam_name_entry.delete(0, tk.END)
        year_entry.delete(0, tk.END)
        exam_value_entry.delete(0, tk.END)
    except ValueError:
        messagebox.showerror("Input Error", "Year must be an integer!")

# Function to export the DataFrame to an Excel file
def export_to_excel():
    if data.empty:
        messagebox.showwarning("No Data", "No data available to export!")
        return
    
    file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
    if file_path:
        try:
            # Specify the engine to ensure compatibility
            data.to_excel(file_path, index=False, engine="openpyxl")
            messagebox.showinfo("Success", f"Data exported to {file_path} successfully!")
        except Exception as e:
            messagebox.showerror("Export Error", f"An error occurred while exporting: {e}")

# Create the main Tkinter window
root = tk.Tk()
root.title("Competitor Exam Data Entry")

# Create input fields and labels
tk.Label(root, text="Competitor Name:").grid(row=0, column=0, padx=10, pady=5)
competitor_name_entry = tk.Entry(root)
competitor_name_entry.grid(row=0, column=1, padx=10, pady=5)

tk.Label(root, text="Exam Name:").grid(row=1, column=0, padx=10, pady=5)
exam_name_entry = tk.Entry(root)
exam_name_entry.grid(row=1, column=1, padx=10, pady=5)

tk.Label(root, text="Year:").grid(row=2, column=0, padx=10, pady=5)
year_entry = tk.Entry(root)
year_entry.grid(row=2, column=1, padx=10, pady=5)

tk.Label(root, text="Exam Value:").grid(row=3, column=0, padx=10, pady=5)
exam_value_entry = tk.Entry(root)
exam_value_entry.grid(row=3, column=1, padx=10, pady=5)

# Create buttons
add_button = tk.Button(root, text="Add to DataFrame", command=add_to_df)
add_button.grid(row=4, column=0, columnspan=2, pady=10)

export_button = tk.Button(root, text="Export to Excel", command=export_to_excel)
export_button.grid(row=5, column=0, columnspan=2, pady=10)

# Run the Tkinter main loop
root.mainloop()


print(data)