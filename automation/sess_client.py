import logging
from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def log_in(driver, username, password):
    """
    Logs into the university system using credentials passed as arguments.
    """
    if not username or not password:
        raise ValueError("SESS_USERNAME and SESS_PASSWORD must be set in the .env file.")
    sess_url = 'https://sess.sku.ac.ir/'
    
    driver.get(sess_url)
    sleep(0.5)

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "edId"))).send_keys(username)
    driver.find_element(By.ID, "edPass").send_keys(password)
    sleep(0.5)
    driver.find_element(By.ID, "edEnter").click()


def navigate_to_registration_page(driver):
    """
    Clicks on "Registration Operations" and retries if registration is not active.
    """
    while True:
        try:
            # Click on "Registration Operations"
            logging.info("🔄 Attempting to enter registration operations...")
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@class='inner' and contains(., 'عملیات ثبت نام')]"))
            ).click()

            # Wait a moment to see if an error message appears
            sleep(1)

            # Check for the CRITICAL "evaluation incomplete" error
            evaluation_error_msg = driver.find_elements(By.XPATH, "//div[@class='toast-message' and contains(text(), 'براي دروس زير ارزيابي انجام نداده ايد')]")
            if evaluation_error_msg:
                logging.critical("❌ ERROR: Registration not allowed due to incomplete course evaluations.")
                raise SystemExit("Incomplete course evaluations.") # Stop the entire script

            # Check for the "registration not active" error
            not_active_error_msg = driver.find_elements(By.XPATH, "//div[@class='toast-message' and contains(text(), 'در حال حاضر ثبت نام برای این دانشجو فعال نیست')]")
            if not_active_error_msg:
                logging.warning("⏳ Registration is not active. Waiting for 10 seconds before retrying...")
                sleep(10)
                continue # Retry the loop

            # If no specific error messages are found, assume success
            logging.info("✅ Successfully entered registration operations.")
            break

        except SystemExit as e:
            # Re-raise the exception to ensure the script stops
            raise e
        except Exception as e:
            # This handles cases where the page changes and the error message can't be found
            logging.info("✅ Successfully entered registration operations (or page changed).")
            break


def get_available_courses(driver, course_list_string):
    """
    Checks if courses are available before attempting to register.
    Returns a filtered list of available courses.
    """
    if not course_list_string:
        logging.warning("⚠️ No courses found in the .env file. Please set the COURSES variable.")
        return [], []
        
    course_list = [course.strip() for course in course_list_string.split(',')]

    available_courses = []
    unavailable_courses = []

    for course_group in course_list:
        course_id = course_group.split(':')[0]
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//td[@class='label-link' and @addnewcrs='{course_id}']")
                )
            )
            available_courses.append(course_group)
        except Exception:
            logging.warning(f"⚠️ Course {course_id} is not available for registration.")
            unavailable_courses.append(course_group)

    return available_courses, unavailable_courses


def handle_system_messages(driver, course_id, group_code, course_group, course_list):
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
            logging.error(f"❌ Registration for course {course_id} with group {group_code} is not allowed. Removing from list.")
            course_list.remove(course_group)
            return True  # Continue process

        # Case 2: Maximum credits reached -> STOP everything!
        elif "تعداد واحد اخذ شده بیش از حد مجاز است" in message_text:
            logging.critical("⚠️ Maximum allowed credits reached! Stopping registration process.")
            return False  # Signal to stop the entire process

        # Case 3: Successfully registered
        elif "ثبت نام در کلاس با موفقیت انجام شد" in message_text:
            logging.info(f"✅ Course {course_id} with group {group_code} successfully registered. Removing from list.")
            course_list.remove(course_group)
            return True  # Continue process

        # Case 4: Time conflict with another course
        elif "برخورد ساعات تشکیل" in message_text:
            logging.warning(f"⏳ Course {course_id} (Group {group_code}) has a scheduling conflict. Removing from list.")
            course_list.remove(course_group)
            return True  # Continue process

    return True  # Default: Continue process


def attempt_course_registration(driver, course_list):
    """
    Handles the automated process of selecting and registering for courses.
    """
    # Continue attempting until all courses are processed
    while course_list:
        for course_group in course_list[:]:  # Iterate over a copy to allow modifications
            
            parts = course_group.split(':')
            course_id = parts[0]
            group_code = parts[1]
            # Set sub_group to the third part if it exists, otherwise default to '0'
            sub_group = parts[2] if len(parts) > 2 else '0'
            
            try:
                # Attempt to select course
                WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, f"//td[@class='label-link' and @addnewcrs='{course_id}']"))
                ).click()

                # Check system messages for errors before selecting group
                if not handle_system_messages(driver, course_id, group_code, course_group, course_list):
                    continue  # Skip further processing if the course was removed

                # Select group
                driver.execute_script(
                    "arguments[0].click();",
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located(
                            (By.XPATH, f"//tr[contains(@ident, ':{course_id}:{group_code}:{sub_group}')]")
                        )
                    )
                )

                logging.info(f"🔄 Attempting to register for course {course_id} (Group {group_code}, Sub-group {sub_group})...")

                # Check system messages for the result
                if not handle_system_messages(driver, course_id, group_code, course_group, course_list):
                    return  # Skip further checks if the course was removed

            except:
                logging.error(f"⚠️ Could not register for {course_id} (Group {group_code})")

        # Check if courses have been taken
        for course_group in course_list[:]:  # Iterate over a copy to allow modifications
            
            parts = course_group.split(':')
            course_id = parts[0]
            group_code = parts[1]

            try:
                WebDriverWait(driver, 5).until(
                    EC.invisibility_of_element_located((By.XPATH, f"//td[@class='label-link' and @addnewcrs='{course_id}']"))
                )
                logging.info(f"✅ Course {course_id} (Group {group_code}) successfully registered.")
                course_list.remove(course_group)

            except:
                logging.info(f"🔄 Course {course_id} (Group {group_code}) is still available. Trying again...")

        if not course_list:
            break  # Exit if all courses are processed

        logging.info(f"⏳ Waiting before the next attempt... {len(course_list)} courses remaining.")
        sleep(0.5)  # Adjust sleep time as needed

    logging.info("🎉 All courses processed successfully!")


def check_unavailable_course_reasons(driver, unavailable_courses):
    """
    Checks the reason why the courses were not seen for registration.
    """
    if not unavailable_courses:
        return
    
    logging.info("\n🔍 Checking the reason why some courses were not available:")
    for course in unavailable_courses:
        course_id = course.split(':')[0]
        try:
            # Find and clear the input field, then enter the course code
            input_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "edCrsCode"))
            )
            input_field.clear()
            input_field.send_keys(course_id)

            # Click the check button
            check_button = driver.find_element(By.ID, "btnCheckCrs")
            check_button.click()

            # Wait for the result to appear in the label and log it
            result_label = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "lblCheckResult"))
            )
            result_text = result_label.text.strip()
            logging.info(f"➡️ Result for course {course_id}: {result_text}")
            sleep(0.5)
        except Exception as e:
            logging.error(f"⚠️ Error checking course {course_id}: {e}")