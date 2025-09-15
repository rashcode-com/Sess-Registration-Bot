from Sess import *
from selenium import webdriver

if __name__ == '__main__':
    # automatically manage the ChromeDriver installation
    driver = webdriver.Chrome()

    # Log in to the university system using credentials from 'user_pass.txt'
    logIn(driver)

    # Navigate to the registration operations page
    registrationOperations(driver)

    # Check which courses are available and which are not
    available_courses, unavailable_courses = checkAvailableCourses(driver)

    # Automatically attempt to register for available courses
    courseSelectionProcess(driver, available_courses)

    # Check and print the reasons why certain courses are unavailable
    checkCourseReason(driver, unavailable_courses)

    # Wait for user input before closing the browser
    input("Press Enter to close the browser...")

    # Close the browser and end the session
    driver.quit()