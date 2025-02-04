from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from time import sleep

def logIn(driver):
    sess = 'https://sess.sku.ac.ir/'
    user_pass = []
    with open('user_pass.txt', 'r') as file:
        user_pass.append(file.readline().strip())
        user_pass.append(file.readline().strip())

    driver.get(sess)
    sleep(0.5)

    # Use WebDriverWait for better synchronization
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "edId"))).send_keys(user_pass[0])
    driver.find_element(By.ID, "edPass").send_keys(user_pass[1])
    sleep(0.5)
    driver.find_element(By.ID, "edEnter").click()

    # Proceed to course selection process
    registerCourses(driver)

def getAvailableCourses(driver):
    """
    This function retrieves the list of available courses from the system
    and filters out the courses that are not offered.
    """
    # Click on the "Registration Operations" button
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//div[@class='inner' and contains(., 'عملیات ثبت نام')]"))
    ).click()

    # Read the list of requested courses from file
    requested_units = []
    with open('UnitsList.txt', 'r') as file:
        requested_units = [line.strip() for line in file.readlines()]

    # Get all offered courses from the page
    available_units = []
    elements = driver.find_elements(By.XPATH, "//td[@class='label-link']")
    for elem in elements:
        available_units.append(elem.get_attribute("addnewcrs"))

    # Check which requested courses are actually available
    valid_units = []
    for unit_group in requested_units:
        unit, group_code = unit_group.split(':')
        if unit in available_units:
            valid_units.append(unit_group)  # Keep only valid courses
        else:
            print(f"Course {unit} is not available.")

    return valid_units

def registerCourses(driver):
    # Get the final list of available courses
    unit_numbers = getAvailableCourses(driver)

    # Stop the process if no courses are available
    if not unit_numbers:
        print("No available courses to register. Process stopped.")
        return

    # Main loop to register for courses
    while unit_numbers:
        # First attempt: request registration for all courses
        for unit_group in unit_numbers:
            try:
                unit, group_code = unit_group.split(':')

                # Try selecting the course
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, f"//td[@class='label-link' and @addnewcrs='{unit}']"))
                ).click()

                # Select the specified group for the course
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, f"//tr[contains(@ident, '14032:{unit}:{group_code}:0')]"))
                ).click()

                print(f"Attempting to register for course {unit} with group {group_code}.")

            except Exception as e:
                print(f"Error processing course {unit_group}: {e}")

        # Check if any courses were successfully registered
        for unit_group in unit_numbers[:]:  # Iterate over a copy of the list for safe modification
            unit, group_code = unit_group.split(':')

            try:
                # Verify if the course is still visible (not registered yet)
                WebDriverWait(driver, 5).until(
                    EC.invisibility_of_element_located((By.XPATH, f"//td[@class='label-link' and @addnewcrs='{unit}']"))
                )
                # If the course is no longer visible, it means registration was successful
                print(f"Course {unit} with group {group_code} has been successfully registered.")
                unit_numbers.remove(unit_group)

            except Exception as e:
                # If the course is still visible, retry in the next iteration
                print(f"Course {unit} with group {group_code} is still available. Retrying...")

        # Wait before the next registration attempt to reduce server load
        print(f"Waiting before the next attempt... {len(unit_numbers)} courses remaining.")
        sleep(2)

    print("All courses have been processed successfully.")
