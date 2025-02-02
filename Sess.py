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
    # Wait for the first element to be clickable and click it
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//div[@class='inner' and contains(., 'عملیات ثبت نام')]"))).click()

    # Wait for the second element to be clickable and click it
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//td[@class='label-link' and @addnewcrs='150730006']"))).click()

    # Wait for the third element to be clickable and click it
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//tr[contains(@ident, '14032:150730006:2:0')]"))).click()