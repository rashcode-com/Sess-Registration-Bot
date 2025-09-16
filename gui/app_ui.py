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
        msg = self.format(record)
        self.text_widget.log(msg)

class RegistrationBotUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SESS Registration Bot")
        self.root.geometry("500x600")
        self.driver = None
        self.course_entries = []

        # --- Frames ---
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        credentials_frame = ttk.LabelFrame(main_frame, text="Login Information", padding="10")
        credentials_frame.pack(fill=tk.X, pady=5)
        
        self.courses_frame = ttk.LabelFrame(main_frame, text="Course List", padding="10")
        self.courses_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        actions_frame = ttk.Frame(main_frame)
        actions_frame.pack(fill=tk.X, pady=10)

        log_frame = ttk.LabelFrame(main_frame, text="Operation Log", padding="10")
        log_frame.pack(fill=tk.X, pady=5)

        # --- Credentials Widgets ---
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.semester_var = tk.StringVar()

        ttk.Label(credentials_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(credentials_frame, textvariable=self.username_var, width=30).grid(row=0, column=1, sticky=tk.EW)
        
        ttk.Label(credentials_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(credentials_frame, textvariable=self.password_var, show="*", width=30).grid(row=1, column=1, sticky=tk.EW)

        ttk.Label(credentials_frame, text="Semester Code:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(credentials_frame, textvariable=self.semester_var, width=30).grid(row=2, column=1, sticky=tk.EW)
        
        credentials_frame.columnconfigure(1, weight=1)

        # --- Course List Widgets ---
        self.add_course_button = ttk.Button(self.courses_frame, text="Add Course", command=self.add_course_entry)
        self.add_course_button.pack(pady=5)
        
        self.course_entry_frame = ttk.Frame(self.courses_frame)
        self.course_entry_frame.pack(fill=tk.BOTH, expand=True)

        # --- Action Widgets ---
        self.start_button = ttk.Button(actions_frame, text="Start Registration", command=self.start_registration_thread)
        self.start_button.pack(fill=tk.X)

        # --- Log Widgets ---
        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=8)
        self.log_area.pack(fill=tk.X, expand=True)
        self.log_area.configure(state='disabled')

        # --- Configure Logging ---
        # Set up the custom handler to redirect all logs to this UI
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(TkinterLogHandler(self))
        # Silence noisy selenium logs
        logging.getLogger('selenium').setLevel(logging.ERROR)

        # --- Load .env ---
        self.load_or_create_env()

    def log(self, message):
        """ Appends a message to the log area safely from any thread. """
        self.root.after(0, self._log_message, message)

    def _log_message(self, message):
        self.log_area.configure(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.configure(state='disabled')

    def add_course_entry(self, course_text=""):
        """ Dynamically adds a new entry field for a course. """
        frame = ttk.Frame(self.course_entry_frame)
        frame.pack(fill=tk.X, pady=2)
        
        entry = ttk.Entry(frame, width=40)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        entry.insert(0, course_text)
        
        remove_btn = ttk.Button(frame, text="-", width=2, command=lambda f=frame: f.destroy())
        remove_btn.pack(side=tk.RIGHT, padx=5)
        
        self.course_entries.append(entry)

    def load_or_create_env(self):
        """ Loads data from .env or creates the file if it doesn't exist. """
        if not os.path.exists(ENV_FILE):
            with open(ENV_FILE, "w") as f:
                f.write("# SESS Bot Configuration\n")
            logging.info(f"Created {ENV_FILE} file.")
        
        load_dotenv(dotenv_path=ENV_FILE)
        self.username_var.set(os.getenv("SESS_USERNAME", ""))
        self.password_var.set(os.getenv("SESS_PASSWORD", ""))
        self.semester_var.set(os.getenv("SEMESTER", ""))
        
        courses_str = os.getenv("COURSES", "")
        if courses_str:
            for course in courses_str.split(','):
                self.add_course_entry(course.strip())
        logging.info("Loaded settings from .env file.")

    def save_env(self):
        """ Saves current GUI settings to the .env file. """
        course_list = [entry.get().strip() for entry in self.course_entries if entry.winfo_exists() and entry.get().strip()]
        courses_str = ",".join(course_list)

        set_key(ENV_FILE, "SESS_USERNAME", self.username_var.get())
        set_key(ENV_FILE, "SESS_PASSWORD", self.password_var.get())
        set_key(ENV_FILE, "SEMESTER", self.semester_var.get())
        set_key(ENV_FILE, "COURSES", courses_str)
        logging.info("Settings saved to .env file.")

    def start_registration_thread(self):
        """ Validates input, saves settings, and starts the automation thread. """
        if not self.username_var.get() or not self.password_var.get() or not self.semester_var.get():
            messagebox.showerror("Error", "Please fill in Username, Password, and Semester Code.")
            return

        self.save_env()
        self.start_button.config(state=tk.DISABLED, text="Running...")
        
        thread = threading.Thread(target=self.registration_worker)
        thread.daemon = True
        thread.start()

    def registration_worker(self):
        """ The worker function that runs the Selenium automation. """
        try:
            logging.info("\n--- Starting Registration Process ---")
            
            username = self.username_var.get()
            password = self.password_var.get()
            semester = self.semester_var.get()
            course_list_from_entries = [entry.get().strip() for entry in self.course_entries if entry.winfo_exists() and entry.get().strip()]
            courses_str = ",".join(course_list_from_entries)

            if not courses_str:
                logging.error("Error: No courses entered for registration.")
                messagebox.showerror("Error", "No courses have been added to the list.")
                return

            self.driver = webdriver.Chrome()

            log_in(self.driver, username, password)
            navigate_to_registration_page(self.driver)
            
            available_courses, unavailable_courses = get_available_courses(self.driver, courses_str)
            logging.info(f"Found {len(available_courses)} available courses for registration attempt.")

            if available_courses:
                attempt_course_registration(self.driver, available_courses, semester)
            
            if unavailable_courses:
                check_unavailable_course_reasons(self.driver, unavailable_courses)

            logging.info("\n🎉 Process finished successfully.")
            messagebox.showinfo("Process Finished", "The registration process is complete. Check the log for details.")

        except Exception as e:
            logging.error(f"❌ An unexpected error occurred: {e}")
            messagebox.showerror("Critical Error", f"The process failed with an error: {e}")
        finally:
            if self.driver:
                self.driver.quit()
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL, text="Start Registration"))