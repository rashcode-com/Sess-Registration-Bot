from Sess import *
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

if __name__ == '__main__':
    # Use webdriver-manager
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    logIn(driver)
    input("Press Enter to close the browser...")
    driver.quit()