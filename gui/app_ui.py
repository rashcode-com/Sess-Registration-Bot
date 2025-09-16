import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import logging
from dotenv import load_dotenv, set_key
from selenium import webdriver

# Import the automation functions
from automation import (
    log_in,
    navigate_to_registration_page,
    get_available_courses,
    attempt_course_registration,
    check_unavailable_course_reasons
)

ENV_FILE = ".env"

# Custom logging handler to redirect logs to a Tkinter widget


class TkinterLogHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        # Format the log record and pass it to the Tkinter log method
        msg = self.format(record)
        self.text_widget.log(msg)


class RegistrationBotUI:
    def __init__(self, root):
        # Initialize main window
        self.root = root
        self.root.title("SESS Registration Bot")
        self.root.geometry("500x600")
        self.driver = None
        self.course_entries = []
        self.course_rows = []

        # --- Frames ---
        # Main container for all UI sections
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Credentials input frame
        credentials_frame = ttk.LabelFrame(
            main_frame, text="Login Information", padding="10")
        credentials_frame.pack(fill=tk.X, pady=5)

        # Course list section
        self.courses_frame = ttk.LabelFrame(
            main_frame, text="Course List", padding="10")
        self.courses_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Action buttons frame
        actions_frame = ttk.Frame(main_frame)
        actions_frame.pack(fill=tk.X, pady=10)

        # Log output section
        log_frame = ttk.LabelFrame(
            main_frame, text="Operation Log", padding="10")
        log_frame.pack(fill=tk.X, pady=5)

        # --- Credentials Widgets ---
        # Input fields for username, password, semester
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.semester_var = tk.StringVar()

        ttk.Label(credentials_frame, text="Username:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(credentials_frame, textvariable=self.username_var,
                  width=30).grid(row=0, column=1, sticky=tk.EW)

        ttk.Label(credentials_frame, text="Password:").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(credentials_frame, textvariable=self.password_var,
                  show="*", width=30).grid(row=1, column=1, sticky=tk.EW)

        ttk.Label(credentials_frame, text="Semester Code:").grid(
            row=2, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(credentials_frame, textvariable=self.semester_var,
                  width=30).grid(row=2, column=1, sticky=tk.EW)

        credentials_frame.columnconfigure(1, weight=1)

        # --- Course List Widgets ---
        # Button to add new courses dynamically
        self.add_course_button = ttk.Button(
            self.courses_frame, text="Add Course", command=self.add_course_entry)
        self.add_course_button.pack(pady=5)

        # Header row for course table
        header_frame = ttk.Frame(self.courses_frame)
        header_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
        ttk.Label(header_frame, text="Unit Code", width=25).pack(
            side=tk.LEFT, expand=True)
        ttk.Label(header_frame, text="Group", width=10).pack(
            side=tk.LEFT, expand=True)
        ttk.Label(header_frame, text="Subgroup", width=10).pack(
            side=tk.LEFT, expand=True)
        # Spacer for remove button
        ttk.Label(header_frame, text="", width=5).pack(side=tk.RIGHT)

        # Container for dynamically added course rows
        self.course_entry_frame = ttk.Frame(self.courses_frame)
        self.course_entry_frame.pack(fill=tk.BOTH, expand=True)

        # --- Action Widgets ---
        # Start registration button
        self.start_button = ttk.Button(
            actions_frame, text="Start Registration", command=self.start_registration_thread)
        self.start_button.pack(fill=tk.X)

        # --- Log Widgets ---
        # Scrollable log output area
        self.log_area = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, height=8)
        self.log_area.pack(fill=tk.X, expand=True)
        self.log_area.configure(state='disabled')

        # --- Configure Logging ---
        # Attach custom Tkinter log handler to root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(TkinterLogHandler(self))
        # Silence noisy selenium logs
        logging.getLogger('selenium').setLevel(logging.ERROR)

        # --- Load .env ---
        self.load_or_create_env()

    def log(self, message):
        """ Append a message to the log area safely from any thread. """
        self.root.after(0, self._log_message, message)

    def _log_message(self, message):
        # Insert a new log line into the text widget
        self.log_area.configure(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.configure(state='disabled')

    def add_course_entry(self, unit="", group="", subgroup=""):
        """ Dynamically adds a new row of entry fields for a course. """
        row_frame = ttk.Frame(self.course_entry_frame)
        row_frame.pack(fill=tk.X, pady=2, padx=5)

        # Input fields for unit, group, and subgroup
        unit_entry = ttk.Entry(row_frame, width=25)
        unit_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))
        unit_entry.insert(0, unit)

        group_entry = ttk.Entry(row_frame, width=10)
        group_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        group_entry.insert(0, group)

        subgroup_entry = ttk.Entry(row_frame, width=10)
        subgroup_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        subgroup_entry.insert(0, subgroup)

        # Button to remove the row
        remove_btn = ttk.Button(
            row_frame, text="-", width=3, command=lambda f=row_frame: f.destroy())
        remove_btn.pack(side=tk.RIGHT, padx=(2, 0))

        self.course_rows.append((unit_entry, group_entry, subgroup_entry))

    def load_or_create_env(self):
        """ Loads data from .env or creates the file if it doesn't exist. """
        if not os.path.exists(ENV_FILE):
            # Create a new .env file if missing
            with open(ENV_FILE, "w") as f:
                f.write("# SESS Bot Configuration\n")
            logging.info(f"Created {ENV_FILE} file.")

        # Load environment variables into memory
        load_dotenv(dotenv_path=ENV_FILE)
        self.username_var.set(os.getenv("SESS_USERNAME", ""))
        self.password_var.set(os.getenv("SESS_PASSWORD", ""))
        self.semester_var.set(os.getenv("SEMESTER", ""))

        # Parse course entries from the environment variable
        courses_str = os.getenv("COURSES", "")
        if courses_str:
            for course in courses_str.split(','):
                parts = course.strip().split(':')
                unit = parts[0] if len(parts) > 0 else ""
                group = parts[1] if len(parts) > 1 else ""
                subgroup = parts[2] if len(parts) > 2 else ""
                self.add_course_entry(unit, group, subgroup)

        logging.info("Loaded settings from .env file.")

    def save_env(self):
        """ Saves current GUI settings to the .env file. Returns the courses string. """
        course_list = []
        for unit_entry, group_entry, subgroup_entry in self.course_rows:
            if not unit_entry.winfo_exists():
                continue  # Skip destroyed rows

            unit = unit_entry.get().strip()
            group = group_entry.get().strip()
            subgroup = subgroup_entry.get().strip()

            # Only save if unit and group are provided
            if unit and group:
                if subgroup:
                    course_list.append(f"{unit}:{group}:{subgroup}")
                else:
                    course_list.append(f"{unit}:{group}")

        courses_str = ",".join(course_list)

        # Save all values into the .env file
        set_key(ENV_FILE, "SESS_USERNAME", self.username_var.get())
        set_key(ENV_FILE, "SESS_PASSWORD", self.password_var.get())
        set_key(ENV_FILE, "SEMESTER", self.semester_var.get())
        set_key(ENV_FILE, "COURSES", courses_str)
        logging.info("Settings saved to .env file.")
        return courses_str

    def start_registration_thread(self):
        """ Validates input, saves settings, and starts the automation thread. """
        if not all([self.username_var.get(), self.password_var.get(), self.semester_var.get()]):
            messagebox.showerror(
                "Error", "Please fill in Username, Password, and Semester Code.")
            return

        courses_str = self.save_env()  # Save settings and get the course string
        if not courses_str:
            messagebox.showwarning(
                "Warning", "No courses have been added to the list.")
            return

        # Disable the start button to prevent duplicate clicks
        self.start_button.config(state=tk.DISABLED, text="Running...")

        # Run Selenium automation in a background thread
        thread = threading.Thread(
            target=self.registration_worker, args=(courses_str,))
        thread.daemon = True
        thread.start()

    def registration_worker(self, courses_str):
        """ The worker function that runs the Selenium automation. """
        try:
            logging.info("\n--- Starting Registration Process ---")

            username = self.username_var.get()
            password = self.password_var.get()
            semester = self.semester_var.get()

            # Launch Chrome WebDriver
            self.driver = webdriver.Chrome()

            # Perform the automated steps
            log_in(self.driver, username, password)
            navigate_to_registration_page(self.driver)

            # Fetch available/unavailable courses
            available_courses, unavailable_courses = get_available_courses(
                self.driver, courses_str)
            logging.info(
                f"Found {len(available_courses)} available courses for registration attempt.")

            # Try to register available courses
            if available_courses:
                attempt_course_registration(
                    self.driver, available_courses, semester)

            # Log reasons for unavailable courses
            if unavailable_courses:
                check_unavailable_course_reasons(
                    self.driver, unavailable_courses)

            logging.info("\n🎉 Process finished successfully.")
            messagebox.showinfo(
                "Process Finished", "The registration process is complete. Check the log for details.")

        except Exception as e:
            logging.error(f"❌ An unexpected error occurred: {e}")
            messagebox.showerror(
                "Critical Error", f"The process failed with an error: {e}")
        finally:
            # Always clean up the WebDriver
            if self.driver:
                self.driver.quit()
            # Re-enable the start button
            self.root.after(0, lambda: self.start_button.config(
                state=tk.NORMAL, text="Start Registration"))
