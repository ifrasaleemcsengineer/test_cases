from selenium import webdriver
from selenium.webdriver.common.keys import Keys

webdriver_path = "/home/all/Downloads/chromedriver_linux64/chromedriver"  # Replace with the actual path

# Step 1: Open the web browser
driver = webdriver.Chrome(executable_path=webdriver_path)

# Step 2: Navigate to the Gmail website
driver.get("https://mail.google.com")

# Step 3: Enter a valid email address
email_field = driver.find_element_by_id("identifierId")
email_field.send_keys("ifrasaleemcsengineer12@gmail.com")

next_button = driver.find_element_by_id("identifierNext")
next_button.click()

# Step 4: Enter a valid password
password_field = driver.find_element_by_name("password")
password_field.send_keys("s@")

# Step 5: Click on the "Next" button
next_button = driver.find_element_by_id("identifierNext")
next_button.click()

# Step 6: Wait for the login process to complete
driver.implicitly_wait(5)  # Wait for 5 seconds

# Verification: Check if user is redirected to the Gmail inbox page
if "inbox" in driver.current_url:
    print("Login successful. Redirected to Gmail inbox.")
else:
    print("Login failed. Not redirected to Gmail inbox.")

# Close the web browser
driver.quit()