from selenium import webdriver

# Open the web browser
driver = webdriver.Chrome()

# Navigate to the Gmail website
driver.get("https://www.gmail.com")

# Enter a valid email address in the email field
email_field = driver.find_element_by_id("email_field_id")
email_field.send_keys("user@example.com")

# Enter a valid password in the password field
password_field = driver.find_element_by_id("password_field_id")
password_field.send_keys("********")

# Click on the "Next" or "Sign in" button
next_button = driver.find_element_by_id("next_button_id")
next_button.click()

# Verify that the user is redirected to the Gmail inbox
assert driver.current_url == "https://mail.google.com/inbox"

# Close the web browser
driver.quit()