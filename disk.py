import os
import threading
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import hashlib
import shutil
from tkinter import ttk
import collections
from PIL import Image, ImageTk
from tkinter import dialog  # Import the 'ttk' module for themed widgets
import matplotlib.pyplot as plt
from collections import defaultdict

# Create the main application window
app = tk.Tk()
app.title("Disk Space Manager")
app.geometry("610x640")
app.configure(bg="#8B9FCF")
# Set a custom style for the widgets
style = ttk.Style()
style.theme_use("xpnative")  # Choose a theme for better appearance (options: "clam", "alt", "default", etc.)
style.configure("TButton", font=("Helvetica", 12), padding=5, relief=tk.RAISED, background="pink", foreground="black")


def get_disk_usage(path):
    total = 0
    try:
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += get_disk_usage(entry.path)
    except PermissionError:
        print(" ")
    return total



def get_free_space(path):
    if os.name == 'posix':  # Unix-like system
        statvfs = os.statvfs(path)
        free_space = statvfs.f_frsize * statvfs.f_bavail
    else:  # Windows
        free_space = shutil.disk_usage(path).free
    return free_space

def format_size(size):
     for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0



        
        
def list_disk_usage():
    path = path_entry.get()
    if os.path.isdir(path):
        def list_disk_usage_task():
            total_size = get_disk_usage(path)
            free_space = get_free_space(path)
            result = (
                f"Disk Space Usage at '{path}':\n"
                f"Total Size of selected folder is : {format_size(total_size)}\n"
                f"Total Free Space in your disk is: {format_size(free_space)}\n"
            )
            app.after(0, update_gui_with_results, result)

        threading.Thread(target=list_disk_usage_task).start()
    else:
        update_gui_with_results(f"Invalid path: '{path}'\n")








def delete_file():
    file_path = file_entry.get()
    if os.path.isfile(file_path):
        # Function to handle the deletion of the file after confirmation
        def perform_deletion():
            try:
                os.remove(file_path)
                update_gui_with_results(f"File '{file_path}' deleted successfully.")
            except OSError as e:
                update_gui_with_results(f"Error deleting file: {e}")

        # Function to show the confirmation pop-up
        def show_confirmation_popup():
            result = messagebox.askyesno("Confirmation", f"Are you sure to delete the selected file: {file_path}?")
            if result:
                # If user clicks Yes, proceed with the deletion task in a separate thread
                threading.Thread(target=perform_deletion).start()

        # Show the confirmation pop-up
        show_confirmation_popup()
    else:
        update_gui_with_results(f"Invalid file path: '{file_path}'")


def display_least_frequently_used_files():
    path = path_entry.get()
    if os.path.isdir(path):
        def scan_files_usage(current_path):
            file_usage_count = collections.defaultdict(int)

            for root, dirs, files in os.walk(current_path):
                for entry in files:
                    file_path = os.path.join(root, entry)
                    if os.path.isfile(file_path):
                        file_usage_count[file_path] += 1

            return file_usage_count

        def show_least_frequently_used_files_task():
            usage_counts = scan_files_usage(path)
            least_frequent_files = sorted(usage_counts.keys(), key=lambda x: usage_counts[x])
            num_files_to_display = min(10, len(least_frequent_files))

            least_frequent_files_list = least_frequent_files[:num_files_to_display]
            create_least_frequent_files_dialog(least_frequent_files_list)

        threading.Thread(target=show_least_frequently_used_files_task).start()
    else:
        update_large_files_text(f"Invalid path: '{path}'\n")






def create_least_frequent_files_dialog(least_frequent_files):
    dialog = tk.Toplevel(app)
    dialog.title("Least Frequent used")
    dialog.geometry("600x600")

    selected_files = {}
    file_open_counts = defaultdict(int)  # Dictionary to store the file open counts

    def delete_selected_files():
        result = messagebox.askquestion("Delete Files", "Are you sure you want to delete selected files?")
        if result == "yes":
            def delete_selected_files_task():
                for file_path, var in selected_files.items():
                    if var.get():
                        try:
                            os.remove(file_path)
                            update_large_files_text(f"File '{file_path}' deleted successfully.")
                        except OSError as e:
                            update_large_files_text(f"Error deleting file '{file_path}': {e}")

                dialog.destroy()

            threading.Thread(target=delete_selected_files_task).start()

    def open_file(file_path):
        os.startfile(file_path)
        file_open_counts[file_path] += 1  # Increment the file open count when the file is opened
        update_file_listbox()  # Update the file listbox to show the latest file open counts

    def update_file_listbox():
        # Clear the current file listbox
        for widget in file_listbox.winfo_children():
            widget.destroy()

        for index, file_path in enumerate(least_frequent_files):
            checkbox_var = tk.BooleanVar()
            selected_files[file_path] = checkbox_var

            size = os.path.getsize(file_path)
            formatted_size = format_size(size)

            # Get only the file name from the full file path
            file_name = os.path.basename(file_path)

            # Create the formatted file info string
            file_info = f"File {index + 1}: {file_name} ({formatted_size}) - Opened {file_open_counts[file_path]} times\n"

            # Create a button for each file entry
            open_button = ttk.Button(file_listbox, text="Open", command=lambda path=file_path: open_file(path))
            open_button.grid(row=index, column=0, padx=5, pady=2, sticky="w")

            checkbox = ttk.Checkbutton(file_listbox, variable=checkbox_var)
            checkbox.grid(row=index, column=1, padx=5, pady=2, sticky="w")

            # Insert the file info into the text widget
            text_widget = tk.Text(file_listbox, wrap=tk.WORD, height=1, width=50, font=("Helvetica", 12), foreground="#007bff")
            text_widget.grid(row=index, column=2, padx=5, pady=2, sticky="w")
            text_widget.insert(tk.END, file_info)

            # Highlight the size of the file
            text_widget.tag_configure("file_size", font=("Helvetica", 12, "bold"), foreground="red")

            # Find the start and end index of the file size in the file info string
            start_index = file_info.find("(") + 1
            end_index = file_info.find(")")

            # Apply the "file_size" tag to highlight the file size
            text_widget.tag_add("file_size", f"1.0 + {start_index} chars", f"1.0 + {end_index} chars")

            # Bind a function to the event when the file name is clicked
            text_widget.tag_bind("file_size", "<Button-1>", lambda event, path=file_path: open_file(path))

    def select_all_files():
        for var in selected_files.values():
            var.set(True)

    def deselect_all_files():
        for var in selected_files.values():
            var.set(False)

    def show_chart():
        # Create a bar chart to display the file open counts
        file_paths = list(file_open_counts.keys())
        counts = list(file_open_counts.values())

        plt.barh(file_paths, counts)
        plt.xlabel('Number of Times Opened')
        plt.ylabel('File Path')
        plt.title('File Open Counts')
        plt.tight_layout()
        plt.show()

    file_listbox = ttk.Frame(dialog)
    file_listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    # Initially update the file listbox with the latest file open counts
    update_file_listbox()

    delete_button = ttk.Button(dialog, text="Delete Selected", command=delete_selected_files)
    delete_button.pack(side=tk.TOP, padx=10)
    select_all_button = ttk.Button(dialog, text="Select All", command=select_all_files)
    select_all_button.pack(side=tk.TOP, padx=10)

    deselect_all_button = ttk.Button(dialog, text="Deselect All", command=deselect_all_files)
    deselect_all_button.pack(side=tk.TOP, padx=10)

    show_chart_button = ttk.Button(dialog, text="Show Chart", command=show_chart)
    show_chart_button.pack(side=tk.TOP, padx=10, pady=5)





def show_large_files():
    path = path_entry.get()
    if os.path.isdir(path):
        def show_large_files_task(current_path):
            large_files = []
            threshold_size = 3 * 1024 * 1024  # 3 MB threshold

            for root, dirs, files in os.walk(current_path):
                for entry in files:
                    file_path = os.path.join(root, entry)
                    if os.path.isfile(file_path) and os.path.getsize(file_path) > threshold_size:
                        large_files.append(file_path)
            # sort in decreasing order
            large_files.sort(key=lambda file_path: os.path.getsize(file_path), reverse=True)

            if large_files:
                create_large_files_dialog(large_files)
            else:
                update_large_files_text("No large files (greater than 3 MB) found in the selected folder.")

        dialog = tk.Toplevel(app)
        dialog.title("Large Files")
        dialog.geometry("600x400")

        threading.Thread(target=show_large_files_task, args=(path,)).start()
    else:
        update_large_files_text(f"Invalid path: '{path}'\n")


def create_large_files_dialog(large_files):
    # Function to create a dialog to display large files with checkboxes for deletion
    dialog = tk.Toplevel(app)
    dialog.title("Large Files")
    dialog.geometry("600x600")

    selected_files = {}

    def delete_selected_files():
        def delete_selected_files_task():
            for file_path, var in selected_files.items():
                if var.get():
                    try:
                        os.remove(file_path)
                        update_large_files_text(f"File '{file_path}' deleted successfully.")
                    except OSError as e:
                        update_large_files_text(f"Error deleting file '{file_path}': {e}")

            dialog.destroy()
            
            

        threading.Thread(target=delete_selected_files_task).start()

    canvas = tk.Canvas(dialog)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = ttk.Scrollbar(dialog, command=canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Create a frame to contain the widgets
    text_frame = ttk.Frame(canvas)
    canvas.create_window((0, 0), window=text_frame, anchor=tk.NW)

    for index, file_path in enumerate(large_files):
        checkbox_var = tk.BooleanVar()
        selected_files[file_path] = checkbox_var

        size = os.path.getsize(file_path)
        formatted_size = format_size(size)

        # Get only the file name from the full file path
        file_name = os.path.basename(file_path)

        # Create the formatted file info string
        file_info = f"File {index + 1}: {file_name} ({formatted_size})\n"

        # Create a button for each file entry
        open_button = ttk.Button(text_frame, text="Open", command=lambda path=file_path: open_file(path))
        open_button.grid(row=index, column=0, padx=5, pady=2, sticky="w")

        checkbox = ttk.Checkbutton(text_frame, variable=checkbox_var)
        checkbox.grid(row=index, column=1, padx=5, pady=2, sticky="w")

        # Insert the file info into the text widget
        text_widget = tk.Text(text_frame, wrap=tk.WORD, height=1, width=50, font=("Helvetica", 12), foreground="#007bff")
        text_widget.grid(row=index, column=2, padx=5, pady=2, sticky="w")
        text_widget.insert(tk.END, file_info)

        # Highlight the size of the file
        text_widget.tag_configure("file_size", font=("Helvetica", 12, "bold"), foreground="red")

        # Find the start and end index of the file size in the file info string
        start_index = file_info.find("(") + 1
        end_index = file_info.find(")")

        # Apply the "file_size" tag to highlight the file size
        text_widget.tag_add("file_size", f"1.0 + {start_index} chars", f"1.0 + {end_index} chars")

        # Bind a function to the event when the file name is clicked
        text_widget.tag_bind("file_size", "<Button-1>", lambda event, path=file_path: open_file(path))

    # Adjust the scroll region of the canvas to show the entire frame
    text_frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

    delete_button = ttk.Button(dialog, text="Delete Selected", command=delete_selected_files)
    delete_button.pack(pady=10)

    # Configure the canvas to work with the scrollbar
    canvas.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=canvas.yview)

    
def open_file(file_path):
    os.startfile(file_path)
    
    
    



def find_duplicate_files():
    # Function to find duplicate files in the selected directory
    path = path_entry.get()
    if os.path.isdir(path):
        def find_duplicate_files_task():
            file_hashes = {}
            duplicate_files = []

            with os.scandir(path) as entries:
                for entry in entries:
                    if entry.is_file():
                        file_hash = calculate_file_hash(entry.path)
                        if file_hash in file_hashes:
                            duplicate_files.append((file_hashes[file_hash], entry.path))
                        else:
                            file_hashes[file_hash] = entry.path

            if duplicate_files:
                create_duplicate_files_dialog(duplicate_files)
            else:
                update_gui_with_results("No duplicate files found in the selected folder.")
        loading_screen = show_loading_screen()
        threading.Thread(target=find_duplicate_files_task).start()
        loading_screen.after(2000, loading_screen.destroy)
    else:
        update_gui_with_results(f"Invalid path: '{path}'\n")

def calculate_file_hash(file_path):
    # Function to calculate the SHA-256 hash of a file
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as file:
        while chunk := file.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

def create_duplicate_files_dialog(duplicate_files):
    # Function to create a dialog to display duplicate files with checkboxes for deletion
    dialog = tk.Toplevel(app)
    dialog.title("Duplicate Files")
    dialog.geometry("600x400")

    selected_files = {}

    def delete_selected_files():
        def delete_selected_files_task():
            for file_path, var in selected_files.items():
                if var.get():
                    try:
                        os.remove(file_path)
                        update_large_files_text(f"File '{file_path}' deleted successfully.")
                    except OSError as e:
                        update_large_files_text(f"Error deleting file '{file_path}': {e}")

            dialog.destroy()

        threading.Thread(target=delete_selected_files_task).start()

    def select_all_files():
        for var in selected_files.values():
            var.set(True)

    def deselect_all_files():
        for var in selected_files.values():
            var.set(False)

    text_widget = tk.Text(dialog, wrap=tk.WORD, height=15, width=50)
    text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Create a scrollbar for the text widget
    scrollbar = ttk.Scrollbar(dialog, command=text_widget.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Configure the text widget to work with the scrollbar
    text_widget.config(yscrollcommand=scrollbar.set)

    for index, (original_file, duplicate_file) in enumerate(duplicate_files):
        checkbox_var = tk.BooleanVar()
        selected_files[duplicate_file] = checkbox_var

        text_widget.insert(tk.END, f"Original File {index + 1}: {original_file}\n", "bold")
        text_widget.insert(tk.END, f"Duplicate File: {duplicate_file}\n")

        checkbox = ttk.Checkbutton(dialog, variable=checkbox_var)
        checkbox.pack(anchor=tk.W)

    delete_button = ttk.Button(dialog, text="Delete Selected", command=delete_selected_files)
    delete_button.pack(pady=10)

    select_all_button = ttk.Button(dialog, text="Select All", command=select_all_files)
    select_all_button.pack(side=tk.LEFT, padx=10)

    deselect_all_button = ttk.Button(dialog, text="Deselect All", command=deselect_all_files)
    deselect_all_button.pack(side=tk.LEFT, padx=10)


major_file_extensions = [
    ".py", ".txt", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".mp3", ".mp4", ".avi", ".mkv"
]

def scan_specific_file_types():
    path = path_entry.get()
    if os.path.isdir(path):
        def scan_specific_file_types_task(current_path):
            extension = file_type_var.get()
            matching_files = []
            
            for root, dirs, files in os.walk(current_path):
                for entry in files:
                    file_path = os.path.join(root, entry)
                    if os.path.isfile(file_path) and entry.endswith(extension):
                        matching_files.append(file_path)

            if matching_files:
                create_matching_files_dialog(matching_files)
            else:
                update_large_files_text(f"No files with the extension '{extension}' found in the selected folder.")

        threading.Thread(target=scan_specific_file_types_task, args=(path,)).start()
    else:
        update_large_files_text(f"Invalid path: '{path}'\n")


def create_matching_files_dialog(matching_files):
    dialog = tk.Toplevel(app)
    dialog.title("Matching Files")
    dialog.geometry("600x600")

    selected_files = {}

    def delete_selected_files():
        result = messagebox.askquestion("Delete Files", "Are you sure you want to delete selected files?")
        if result == "yes":
            def delete_selected_files_task():
                for file_path, var in selected_files.items():
                    if var.get():
                        try:
                            os.remove(file_path)
                            update_large_files_text(f"File '{file_path}' deleted successfully.")
                        except OSError as e:
                            update_large_files_text(f"Error deleting file '{file_path}': {e}")

                dialog.destroy()

            threading.Thread(target=delete_selected_files_task).start()


    def open_file(file_path):
        os.startfile(file_path)
        
    canvas = tk.Canvas(dialog)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    text_frame = ttk.Frame(canvas)
    canvas.create_window((0, 0), window=text_frame, anchor=tk.NW)


    scrollbar = ttk.Scrollbar(dialog, command=canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)    

      
    for index, file_path in enumerate(matching_files):
        checkbox_var = tk.BooleanVar()
        selected_files[file_path] = checkbox_var

        size = os.path.getsize(file_path)
        formatted_size = format_size(size)

        # Get only the file name from the full file path
        file_name = os.path.basename(file_path)

        # Create the formatted file info string
        file_info = f"File {index + 1}: {file_name} ({formatted_size})\n"

        # Create a button for each file entry
        open_button = ttk.Button(text_frame, text="Open", command=lambda path=file_path: open_file(path))
        open_button.grid(row=index, column=0, padx=5, pady=2, sticky="w")

        checkbox = ttk.Checkbutton(text_frame, variable=checkbox_var)
        checkbox.grid(row=index, column=1, padx=5, pady=2, sticky="w")

        # Insert the file info into the text widget
        text_widget = tk.Text(text_frame, wrap=tk.WORD, height=1, width=50, font=("Helvetica", 12), foreground="#007bff")
        text_widget.grid(row=index, column=2, padx=5, pady=2, sticky="w")
        text_widget.insert(tk.END, file_info)

        # Highlight the size of the file
        text_widget.tag_configure("file_size", font=("Helvetica", 12, "bold"), foreground="red")

        # Find the start and end index of the file size in the file info string
        start_index = file_info.find("(") + 1
        end_index = file_info.find(")")

        # Apply the "file_size" tag to highlight the file size
        text_widget.tag_add("file_size", f"1.0 + {start_index} chars", f"1.0 + {end_index} chars")

        # Bind a function to the event when the file name is clicked
        text_widget.tag_bind("file_size", "<Button-1>", lambda event, path=file_path: open_file(path))

    # Adjust the scroll region of the canvas to show the entire frame
    text_frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

    delete_button = ttk.Button(dialog, text="Delete Selected", command=delete_selected_files)
    delete_button.pack(side=tk.TOP, anchor=tk.W)


    # Configure the canvas to work with the scrollbar
    canvas.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=canvas.yview)    
        
        
         




def delete_large_files():
    path = path_entry.get()
    if os.path.isdir(path):
        def delete_large_files_task(current_path):
            large_files = []
            threshold_size = 3 * 1024 * 1024  # 3 MB threshold
            
            
            
            for root, dirs, files in os.walk(current_path):
                for entry in files:
                    file_path = os.path.join(root, entry)
                    if entry.is_file() and entry.stat().st_size > threshold_size:
                        large_files.append(entry.path)



            for file_path in large_files:
                try:
                    os.remove(file_path)
                    update_large_files_text(f"File '{file_path}' deleted successfully.")
                except OSError as e:
                    update_large_files_text(f"Error deleting file '{file_path}': {e}")
        loading_screen = show_loading_screen()
        threading.Thread(target=delete_large_files_task).start()
        loading_screen.after(2000, loading_screen.destroy)
    else:
        update_large_files_text(f"Invalid path: '{path}'\n")


def breakdown_space_utilization(path):
    result = {}

    if not os.path.exists(path):
        return f"Path '{path}' does not exist."

    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            file_extension = os.path.splitext(file)[-1].lower()

            # Get the drive name from the file path (Windows only)
            drive_name = os.path.splitdrive(file_path)[0] if os.name == 'nt' else '/'

            # Get the file type based on the file extension
            file_type = "Unknown"
            if file_extension in ('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'):
                file_type = "Video"
            elif file_extension in ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'):
                file_type = "Image"
            elif file_extension in ('.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.pdf', '.txt'):
                file_type = "Document"
            elif file_extension in ('.mp3', '.wav', '.ogg', '.flac', '.aac'):
                file_type = "Audio"
            else:
                file_type = "Other"

            # Update the space utilization breakdown
            if drive_name not in result:
                result[drive_name] = {
                    'total_size': 0,
                    'video_size': 0,
                    'image_size': 0,
                    'document_size': 0,
                    'audio_size': 0,
                    'other_size': 0,
                }

            # Check if the file exists before getting its size
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                result[drive_name]['total_size'] += file_size

                if file_type == "Video":
                    result[drive_name]['video_size'] += file_size
                elif file_type == "Image":
                    result[drive_name]['image_size'] += file_size
                elif file_type == "Document":
                    result[drive_name]['document_size'] += file_size
                elif file_type == "Audio":
                    result[drive_name]['audio_size'] += file_size
                else:
                    result[drive_name]['other_size'] += file_size
   
    return result

def draw_bar_chart(data):
    # Get the first (and only) drive name from the data
    drive_name = list(data.keys())[0]

    # Get the sizes for each category from the data
    video_size = data[drive_name]['video_size']
    image_size = data[drive_name]['image_size']
    document_size = data[drive_name]['document_size']
    audio_size = data[drive_name]['audio_size']
    other_size = data[drive_name]['other_size']

    # Create a list of labels for the x-axis
    categories = ['Video', 'Image', 'Document', 'Audio', 'Other']

    # Create a list of sizes for the y-axis
    sizes = [video_size, image_size, document_size, audio_size, other_size]

    # Set the position of each bar on the x-axis
    x_positions = range(len(categories))

    # Create the bar chart
    plt.bar(x_positions, sizes)

    # Add labels and title
    plt.xlabel('Categories')
    plt.ylabel('Space Size')
    plt.title(f'Space Utilization Breakdown for {drive_name}')

    # Add the category labels to the x-axis
    plt.xticks(x_positions, categories)

    # Display the bar chart
    plt.show()

def show_loading_screen():
    loading_screen = tk.Toplevel(app)
    loading_screen.title("Loading...")
    loading_screen.geometry("300x100")

    # Create a label to display "Loading..."
    loading_label = ttk.Label(loading_screen, text="Loading...", font=("Helvetica", 18))
    loading_label.pack(pady=20)

    return loading_screen


def show_space_utilization():
    path = path_entry.get()
    result = breakdown_space_utilization(path)
    

    if isinstance(result, dict):
        large_files_text.config(state=tk.NORMAL)
        large_files_text.delete("1.0", tk.END)
        for drive, space_info in result.items():
            total_size = format_size(space_info['total_size'])
            video_size = format_size(space_info['video_size'])
            image_size = format_size(space_info['image_size'])
            document_size = format_size(space_info['document_size'])
            audio_size = format_size(space_info['audio_size'])
            other_size = format_size(space_info['other_size'])           
            large_files_text.insert(tk.END, f"Path: {path}\n")
            large_files_text.insert(tk.END, f"Total Size: {total_size}\n")
            large_files_text.insert(tk.END, f"Video Size: {video_size}\n")
            large_files_text.insert(tk.END, f"Image Size: {image_size}\n")
            large_files_text.insert(tk.END, f"Document Size: {document_size}\n")
            large_files_text.insert(tk.END, f"Audio Size: {audio_size}\n")
            large_files_text.insert(tk.END, f"Other Size: {other_size}\n\n")
            
        large_files_text.config(state=tk.DISABLED)
        draw_bar_chart(result)
        
    else:
        large_files_text.config(state=tk.NORMAL)
        large_files_text.delete("1.0", tk.END)
        large_files_text.insert(tk.END, result)
        large_files_text.config(state=tk.DISABLED)

def update_gui_with_results(result):
    large_files_text.config(state=tk.NORMAL)#now we can edit text field
    large_files_text.delete("1.0", tk.END)#delete all the text from 1 character
    large_files_text.insert(tk.END, result)
    large_files_text.config(state=tk.DISABLED)

def browse_path():
    path = filedialog.askdirectory()
    path_entry.delete(0, tk.END)
    path_entry.insert(tk.END, path)

def browse_file():
    file_path = filedialog.askopenfilename()
    file_entry.delete(0, tk.END)
    file_entry.insert(tk.END, file_path)
    
    
def update_large_files_text(result):
    large_files_text.config(state=tk.NORMAL)
    large_files_text.delete("1.0", tk.END)
    large_files_text.insert(tk.END, result)
    large_files_text.config(state=tk.DISABLED)   


def center_window(win):
    win.update_idletasks()
    width = win.winfo_width()
    height = win.winfo_height()
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")


# Set a custom style for the widgets
style = ttk.Style()
style.configure("TButton", font=("Helvetica", 12), padding=5)







def show_main_window():
    app.deiconify()  # Show the main window
    flash_page.destroy()  # Close the flash page


def show_flash_page():
    global flash_page
    flash_page = tk.Toplevel()
    flash_page.title("Flash Page")
    flash_page.geometry("650x550")

    # Load the image
    image_path = "back3.jpg"  # Replace this with the actual path to your image
    image = Image.open(image_path)
    photo = ImageTk.PhotoImage(image)

    # Create a label to display the image
    image_label = tk.Label(flash_page, image=photo)
    image_label.image = photo  # Store a reference to the image to prevent garbage collection
    image_label.pack(padx=50, pady=50)
    
     # Get the screen width and height
    screen_width = flash_page.winfo_screenwidth()
    screen_height = flash_page.winfo_screenheight()

    # Calculate the x and y position to center the flash_page window
    x_position = (screen_width - 650) // 2
    y_position = (screen_height - 550) // 2

    # Set the geometry to center the flash_page window
    flash_page.geometry(f"650x550+{x_position}+{y_position}")

    # Schedule the main window to be shown after 5 seconds (5000 milliseconds)
    app.after(2000, show_main_window)


# Hide the main window initially
app.withdraw()

show_flash_page()





# Define a function to add box shadow to buttons
def add_button_box_shadow(button):
    button.config(borderwidth=0)
    button.bind("<Enter>", lambda event: button.config(bg="#007bff", relief=tk.RAISED))
    button.bind("<Leave>", lambda event: button.config(bg="SystemButtonFace", relief=tk.FLAT))

def animate_button(button):
    button.config(relief=tk.SUNKEN)  # Simulate button press animation
    app.after(100, release_button)

def release_button(button):
    button.config(relief=tk.RAISED) 
center_window(app)



large_files_text = tk.Text(app, width=60, height=10, state=tk.DISABLED)

center_window(app)



def toggle_theme():
    current_bg = app.cget("bg")
    new_bg = "#515353" if current_bg == "#A1CCD1" else "#A1CCD1"
    app.configure(bg=new_bg)
    

        


# Create a button to toggle the theme
toggle_button = tk.Button(app, text="Toggle Theme", command=toggle_theme)
toggle_button.grid(row=11, column=0, padx=11, pady=5, columnspan=5, sticky="we")



# Create GUI elements using themed widgets (ttk)
path_label = ttk.Label(app, text="Enter the directory path:")
path_entry = ttk.Entry(app, width=50)
browse_path_button = ttk.Button(app, text="Browse", command=browse_path)
list_disk_usage_button = ttk.Button(app, text="List Disk Space Usage", command=list_disk_usage)

file_label = ttk.Label(app, text="Enter the path of the file:")
file_entry = ttk.Entry(app, width=50)
browse_file_button = ttk.Button(app, text="Browse", command=browse_file)
delete_file_button = ttk.Button(app, text="Delete File", command=delete_file)

# Create a button to show the least frequently used files
show_least_frequent_button = ttk.Button(app, text="Show Least Frequently Used Files", command=display_least_frequently_used_files)
show_least_frequent_button.grid(row=10, column=0, padx=10, pady=5, columnspan=5, sticky="we")

# New button: Show Large Files
show_large_files_button = ttk.Button(app, text="Show Large Files", command=show_large_files)

# Create a dropdown menu for file extensions
file_type_var = tk.StringVar(app)
file_type_var.set(major_file_extensions[0])  # Set the default file extension
file_type_dropdown = ttk.Combobox(app, values=major_file_extensions, textvariable=file_type_var, state="readonly")

# New button: Scan Specific File Types
scan_specific_button = ttk.Button(app, text="Scan Specific File Types", command=scan_specific_file_types)

# New button: Find Duplicate Files
find_duplicate_files_button = ttk.Button(app, text="Find Duplicate Files", command=find_duplicate_files)

large_files_text = tk.Text(app, width=60, height=10, state=tk.DISABLED)

# New button: Breakdown Space Utilization
breakdown_space_button = ttk.Button(app, text="Breakdown Space Utilization", command=show_space_utilization)


# Place GUI elements on the window using grid

screen_width = app.winfo_screenwidth()
screen_height = app.winfo_screenheight()


# trying to make the app responsive 


if screen_width > 1200 and screen_height > 800:
    path_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
    path_entry.grid(row=1, column=1, padx=5, pady=5, columnspan=3, sticky="we")
    browse_path_button.grid(row=1, column=4, padx=5, pady=5, sticky="e")
    list_disk_usage_button.grid(row=2, column=0, padx=10, pady=5, columnspan=5, sticky="we")

    file_label.grid(row=3, column=0, padx=10, pady=5, sticky="w")
    file_entry.grid(row=3, column=1, padx=5, pady=5, columnspan=3, sticky="we")
    browse_file_button.grid(row=3, column=4, padx=5, pady=5, sticky="e")
    delete_file_button.grid(row=4, column=0, padx=10, pady=5, columnspan=5, sticky="we")
    find_duplicate_files_button.grid(row=5, column=0, padx=10, pady=5, columnspan=5, sticky="we")

    file_type_dropdown.grid(row=6, column=0, padx=10, pady=5, sticky="w")
    scan_specific_button.grid(row=6, column=1, padx=5, pady=5, columnspan=4, sticky="we")
    breakdown_space_button.grid(row=7, column=0, padx=10, pady=5, columnspan=5,sticky="we")
    show_large_files_button.grid(row=8, column=0, padx=10, pady=5, columnspan=5, sticky="we")

    # New changes for the large_files_text widget
    large_files_text.grid(row=9, column=0, padx=10, pady=5, columnspan=5, sticky="we")
else:

    path_label.grid(row=3, column=5, padx=10, pady=5, sticky="w")
    path_entry.grid(row=3, column=1, padx=5, pady=5, columnspan=3, sticky="we")
    browse_path_button.grid(row=3, column=4, padx=5, pady=5, sticky="e")
    list_disk_usage_button.grid(row=4, column=0, padx=10, pady=5, columnspan=5, sticky="we")

    file_label.grid(row=5, column=0, padx=10, pady=5, sticky="w")
    file_entry.grid(row=5, column=1, padx=5, pady=5, columnspan=3, sticky="we")
    browse_file_button.grid(row=5, column=4, padx=5, pady=5, sticky="e")
    delete_file_button.grid(row=6, column=0, padx=10, pady=5, columnspan=5, sticky="we")
    find_duplicate_files_button.grid(row=6, column=0, padx=10, pady=5, columnspan=5, sticky="we")

    file_type_dropdown.grid(row=8, column=0, padx=10, pady=5, sticky="w")
    scan_specific_button.grid(row=8, column=1, padx=5, pady=5, columnspan=4, sticky="we")
    breakdown_space_button.grid(row=9, column=0, padx=10, pady=5, columnspan=5,sticky="we")
    show_large_files_button.grid(row=10, column=0, padx=10, pady=5, columnspan=5, sticky="we")

    # New changes for the large_files_text widget
    large_files_text.grid(row=11, column=0, padx=10, pady=5, columnspan=5, sticky="we")






# Start the main event loop
app.mainloop()