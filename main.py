import os
import sys
import logging
import tkinter as tk
from dotenv import load_dotenv
from selenium import webdriver
from automation import *
from gui.app_ui import RegistrationBotUI


def run_cli():
    """Runs the application in Command-Line Interface (CLI) mode."""

    # Configure root logger for console output
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

    # Reduce noise from the selenium library
    logging.getLogger('selenium').setLevel(logging.ERROR)

    logging.info("--- Running in CLI mode ---")

    # Load environment variables
    load_dotenv()
    username = os.getenv("SESS_USERNAME")
    password = os.getenv("SESS_PASSWORD")
    courses_str = os.getenv("COURSES")
    semester = os.getenv("SEMESTER")

    # Validate that all required variables are present
    if not all([username, password, courses_str, semester]):
        logging.critical(
            "One or more required environment variables are missing in .env file.")
        raise ValueError("Required environment variables are missing.")

    driver = None
    try:
        # automatically manage the ChromeDriver installation
        driver = webdriver.Chrome()

        # Log in to the university system
        log_in(driver, username, password)

        # Navigate to the registration operations page
        navigate_to_registration_page(driver)

        # Check which courses are available
        available_courses, unavailable_courses = get_available_courses(
            driver, courses_str)

        # Automatically attempt to register
        attempt_course_registration(driver, available_courses, semester)

        # Check and print the reasons why certain courses are unavailable
        check_unavailable_course_reasons(driver, unavailable_courses)

        # Wait for user input before closing the browser
        input("Press Enter to close the browser...")

    except SystemExit as e:
        # This exception is raised by navigate_to_registration_page on critical errors
        logging.critical(f"Process terminated: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        if driver:
            driver.quit()
        logging.info("--- CLI mode finished ---")


def run_gui():
    """Launches the Graphical User Interface (GUI) for the application."""
    root = tk.Tk()
    app = RegistrationBotUI(root)
    root.mainloop()


if __name__ == '__main__':
    # Check command-line arguments to decide which mode to run
    if len(sys.argv) > 1 and sys.argv[1].lower() == '--cli':
        run_cli()
    else:
        run_gui()
