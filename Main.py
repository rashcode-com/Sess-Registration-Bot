import os
from dotenv import load_dotenv
from Sess import *
from selenium import webdriver

if __name__ == '__main__':
    # Load environment variables from .env file
    load_dotenv()

    # Read all required variables from the environment
    username = os.getenv("SESS_USERNAME")
    password = os.getenv("SESS_PASSWORD")
    courses_str = os.getenv("COURSES")
    semester = os.getenv("SEMESTER")

    # Validate that all required variables are present
    if not all([username, password, courses_str, semester]):
        raise ValueError("One or more required environment variables (SESS_USERNAME, SESS_PASSWORD, COURSES, SEMESTER) are missing.")

    # automatically manage the ChromeDriver installation
    driver = webdriver.Chrome()

    # Log in to the university system
    log_in(driver, username, password)

    # Navigate to the registration operations page
    navigate_to_registration_page(driver)

    # Check which courses are available
    available_courses, unavailable_courses = get_available_courses(driver, courses_str)

    # Automatically attempt to register
    attempt_course_registration(driver, available_courses, semester)

    # Check and print the reasons why certain courses are unavailable
    check_unavailable_course_reasons(driver, unavailable_courses)

    # Wait for user input before closing the browser
    input("Press Enter to close the browser...")

    # Close the browser and end the session
    driver.quit()