import os
from time import sleep
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Load environment variables from .env file
load_dotenv()

def logIn(driver):
    """
    Logs into the university system using credentials from 'user_pass.txt'.
    """
    sess_url = 'https://sess.sku.ac.ir/'

    # Get username and password from environment variables
    username = os.getenv("SESS_USERNAME")
    password = os.getenv("SESS_PASSWORD")

    if not username or not password:
        raise ValueError("USERNAME and PASSWORD must be set in the .env file.")

    driver.get(sess_url)
    sleep(0.5)

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "edId"))).send_keys(username)
    driver.find_element(By.ID, "edPass").send_keys(password)
    sleep(0.5)
    driver.find_element(By.ID, "edEnter").click()


def registrationOperations(driver):
    """
    Clicks on "Registration Operations" and retries if registration is not active.
    """
    while True:
        try:
            # Click on "Registration Operations"
            print("🔄 Attempting to enter registration operations...")
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@class='inner' and contains(., 'عملیات ثبت نام')]"))
            ).click()

            # Wait a moment to see if an error message appears
            sleep(1)

            # Check for the specific error message
            error_message = driver.find_elements(By.XPATH, "//div[@class='toast-message' and contains(text(), 'در حال حاضر ثبت نام برای این دانشجو فعال نیست')]")

            # Decide what to do based on the message
            if error_message:
                print("⏳ Registration is not active. Waiting for 10 seconds before retrying...")
                sleep(10)
                # The loop will continue, and it will try to click again
            else:
                # If no error message is found, the click was successful
                print("✅ Successfully entered registration operations.")
                break # Exit the loop and continue with the script

        except Exception as e:
            # This handles cases where the page changes and the error message can't be found,
            print("✅ Successfully entered registration operations (or page changed).")
            break # Exit the loop


def checkAvailableCourses(driver):
    """
    Checks if courses are available before attempting to register.
    Returns a filtered list of available courses.
    """
    # Load course list from the .env file
    courses_str = os.getenv("COURSES")
    if not courses_str:
        print("⚠️ No courses found in the .env file. Please set the COURSES variable.")
        return [], []
        
    unit_numbers = [course.strip() for course in courses_str.split(',')]

    available_courses = []
    unavailable_courses = []

    for unit_group in unit_numbers:
        unit = unit_group.split(':')[0]
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//td[@class='label-link' and @addnewcrs='{unit}']")
                )
            )
            available_courses.append(unit_group)
        except Exception:
            print(f"⚠️ Course {unit} is not available for registration.")
            unavailable_courses.append(unit_group)

    return available_courses, unavailable_courses


def checkForMessages(driver, unit, group_code, sub_group, unit_numbers):
    """
    Checks for system messages and handles different cases.
    Returns False if the process should stop.
    """
    sleep(0.5)  # Wait for messages to appear
    messages = driver.find_elements(By.XPATH, "//div[@class='toast-message']")

    for msg in messages:
        message_text = msg.text.strip()

        # Case 1: Not allowed to register
        if "شما اجازه ثبت نام در هیچ کدامشان را ندارید" in message_text:
            print(f"❌ Registration for course {unit} with group {group_code} is not allowed. Removing from list.")
            unit_numbers.remove(f"{unit}:{group_code}:{sub_group}")
            return True  # Continue process

        # Case 2: Maximum credits reached -> STOP everything!
        elif "تعداد واحد اخذ شده بیش از حد مجاز است" in message_text:
            print("⚠️ Maximum allowed credits reached! Stopping registration process.")
            return False  # Signal to stop the entire process

        # Case 3: Successfully registered
        elif "ثبت نام در کلاس با موفقیت انجام شد" in message_text:
            print(f"✅ Course {unit} with group {group_code} successfully registered. Removing from list.")
            unit_numbers.remove(f"{unit}:{group_code}:{sub_group}")
            return True  # Continue process

        # Case 4: Time conflict with another course
        elif "برخورد ساعات تشکیل" in message_text:
            print(f"⏳ Course {unit} (Group {group_code}) has a scheduling conflict. Removing from list.")
            unit_numbers.remove(f"{unit}:{group_code}")
            return True  # Continue process

    return True  # Default: Continue process


def courseSelectionProcess(driver, unit_numbers):
    """
    Handles the automated course selection process.
    """
    # Get the semester code from environment variables
    semester_code = os.getenv("SEMESTER")
    if not semester_code:
        raise ValueError("SEMESTER code must be set in the .env file.")
    
    # Continue attempting until all courses are processed
    while unit_numbers:
        for unit_group in unit_numbers[:]:  # Iterate over a copy to allow modifications
            
            parts = unit_group.split(':')
            unit = parts[0]
            group_code = parts[1]
            # Set sub_group to the third part if it exists, otherwise default to '0'
            sub_group = parts[2] if len(parts) > 2 else '0'
            
            try:
                # Attempt to select course
                WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, f"//td[@class='label-link' and @addnewcrs='{unit}']"))
                ).click()

                # Check system messages for errors before selecting group
                if not checkForMessages(driver, unit, group_code, sub_group, unit_numbers):
                    continue  # Skip further processing if the course was removed

                # Select group
                WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, f"//tr[contains(@ident, '{semester_code}:{unit}:{group_code}:{sub_group}')]"))
                ).click()

                print(f"🔄 Attempting to register for course {unit} (Group {group_code}, Sub-group {sub_group})...")

                # Check system messages for the result
                if not checkForMessages(driver, unit, group_code, sub_group, unit_numbers):
                    return  # Skip further checks if the course was removed

            except:
                print(f"⚠️ Could not register for {unit} (Group {group_code})")

        # Check if courses have been taken
        for unit_group in unit_numbers[:]:  # Iterate over a copy to allow modifications
            
            parts = unit_group.split(':')
            unit = parts[0]
            group_code = parts[1]

            try:
                WebDriverWait(driver, 5).until(
                    EC.invisibility_of_element_located((By.XPATH, f"//td[@class='label-link' and @addnewcrs='{unit}']"))
                )
                print(f"✅ Course {unit} (Group {group_code}) successfully registered.")
                unit_numbers.remove(unit_group)

            except:
                print(f"🔄 Course {unit} (Group {group_code}) is still available. Trying again...")

        print(f"⏳ Waiting before the next attempt... {len(unit_numbers)} courses remaining.")
        sleep(0.5)  # Adjust sleep time as needed

    print("🎉 All courses processed successfully!")


def checkCourseReason(driver, unavailable_courses):
    """
    Checks the reason why the courses were not seen for registration.
    """
    print("\n🔍 Checking the reason why some courses were not available:")
    for course in unavailable_courses:
        unit = course.split(':')[0]
        try:
            # Find and clear the input field, then enter the course code
            input_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "edCrsCode"))
            )
            input_field.clear()
            input_field.send_keys(unit)

            # Click the check button
            check_button = driver.find_element(By.ID, "btnCheckCrs")
            check_button.click()

            # Wait for the result to appear in the label and print it
            result_label = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "lblCheckResult"))
            )
            result_text = result_label.text.strip()
            print(f"➡️ Result for course {unit}: {result_text}")
            sleep(0.5)
        except Exception as e:
            print(f"⚠️ Error checking course {unit}: {e}")