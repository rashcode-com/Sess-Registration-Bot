from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def logIn(driver):
    """
    Logs into the university system using credentials from 'user_pass.txt'.
    """
    sess_url = 'https://sess.sku.ac.ir/'
    user_pass = []

    with open('user_pass.txt', 'r') as file:
        user_pass.append(file.readline().strip())
        user_pass.append(file.readline().strip())

    driver.get(sess_url)
    sleep(0.5)

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "edId"))).send_keys(user_pass[0])
    driver.find_element(By.ID, "edPass").send_keys(user_pass[1])
    sleep(0.5)
    driver.find_element(By.ID, "edEnter").click()


def registrationOperations(driver):
    # Click on "Registration Operations"
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//div[@class='inner' and contains(., 'عملیات ثبت نام')]"))
    ).click()


def checkAvailableCourses(driver):
    """
    Checks if courses are available before attempting to register.
    Returns a filtered list of available courses.
    """
    # Load course list
    with open('UnitsList.txt', 'r') as file:
        unit_numbers = [line.strip() for line in file.readlines()]

    available_courses = []
    unavailable_courses = []

    for unit_group in unit_numbers:
        unit, group_code = unit_group.split(':')
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


def checkForMessages(driver, unit, group_code, unit_numbers):
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
            unit_numbers.remove(f"{unit}:{group_code}")
            return True  # Continue process

        # Case 2: Maximum credits reached -> STOP everything!
        elif "تعداد واحد اخذ شده بیش از حد مجاز است" in message_text:
            print("⚠️ Maximum allowed credits reached! Stopping registration process.")
            return False  # Signal to stop the entire process

        # Case 3: Successfully registered
        elif "ثبت نام در کلاس با موفقیت انجام شد" in message_text:
            print(f"✅ Course {unit} with group {group_code} successfully registered. Removing from list.")
            unit_numbers.remove(f"{unit}:{group_code}")
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
    # Continue attempting until all courses are processed
    while unit_numbers:
        for unit_group in unit_numbers[:]:  # Iterate over a copy to allow modifications
            unit, group_code = unit_group.split(':')

            try:
                # Attempt to select course
                WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, f"//td[@class='label-link' and @addnewcrs='{unit}']"))
                ).click()

                # Check system messages for errors before selecting group
                if not checkForMessages(driver, unit, group_code, unit_numbers):
                    continue  # Skip further processing if the course was removed

                # Select group
                WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, f"//tr[contains(@ident, '14032:{unit}:{group_code}:0')]"))
                ).click()

                print(f"🔄 Attempting to register for course {unit} (Group {group_code})...")

                # Check system messages for the result
                if not checkForMessages(driver, unit, group_code, unit_numbers):
                    return  # Skip further checks if the course was removed

            except:
                print(f"⚠️ Could not register for {unit} (Group {group_code})")

        # Check if courses have been taken
        for unit_group in unit_numbers[:]:  # Iterate over a copy to allow modifications
            unit, group_code = unit_group.split(':')

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
        unit, group_code = course.split(':')
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