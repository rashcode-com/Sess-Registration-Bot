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

    # Use WebDriverWait
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "edId"))).send_keys(user_pass[0])
    driver.find_element(By.ID, "edPass").send_keys(user_pass[1])
    sleep(0.5)
    driver.find_element(By.ID, "edEnter").click()

    # Call the post-login method
    postLoginActions(driver)


def postLoginActions(driver):
    # Click on the "Registration Operations" button
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//div[@class='inner' and contains(., 'عملیات ثبت نام')]"))
    ).click()

    # Read the list of course units and group codes from the file
    unit_numbers = []
    with open('UnitsList.txt', 'r') as file:
        unit_numbers = [line.strip() for line in file.readlines()]

    # Loop until the list is empty
    while unit_numbers:
        # First try: request all courses
        for unit_group in unit_numbers:
            try:
                # Split unit code and group code from the input (unit:group)
                unit, group_code = unit_group.split(':')

                # Try to click on the desired course
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, f"//td[@class='label-link' and @addnewcrs='{unit}']"))
                ).click()

                # Select the correct group for the course
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, f"//tr[contains(@ident, '14032:{unit}:{group_code}:0')]"))
                ).click()

                print(f"Attempting to select course {unit} with group {group_code}.")

            except Exception as e:
                print(f"Error processing course {unit_group}: {e}")

        # Now check if any course is taken
        for unit_group in unit_numbers[:]:  # Iterate over a copy of the list to allow modifications during iteration
            unit, group_code = unit_group.split(':')

            try:
                # Check if the course is still visible (not taken yet)
                WebDriverWait(driver, 5).until(
                    EC.invisibility_of_element_located((By.XPATH, f"//td[@class='label-link' and @addnewcrs='{unit}']"))
                )
                # If course is no longer visible, it's taken, so remove it from the list
                print(f"Course {unit} with group {group_code} has been successfully taken.")
                unit_numbers.remove(unit_group)

            except Exception as e:
                # If the course is still visible, try again later
                print(f"Course {unit} with group {group_code} is still available. Trying again...")

        # Pause for a moment before the next round of requests (optional, to avoid overloading the server)
        print(f"Waiting before next attempt... {len(unit_numbers)} courses remaining.")
        sleep(2)  # Adjust sleep time as needed

    print("All courses processed.")


