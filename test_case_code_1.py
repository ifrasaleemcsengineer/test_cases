from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

# Set up Chrome driver
driver = webdriver.Chrome(ChromeDriverManager().install())

# Test Steps
driver.get("https://accounts.google.com/")
email_input = driver.find_element_by_xpath("//input[@type='email']")
email_input.send_keys("user@gmail.com")
next_button = driver.find_element_by_xpath("//div[@id='identifierNext']")
next_button.click()
password_input = driver.find_element_by_xpath("//input[@type='password']")
password_input.send_keys("password123")
sign_in_button = driver.find_element_by_xpath("//div[@id='passwordNext']")
sign_in_button.click()

# Verify the expected result
expected_url = "https://mail.google.com/"
assert driver.current_url == expected_url

# Close the browser
driver.quit()