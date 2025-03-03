from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

app = Flask(__name__)

@app.route('/apply', methods=['POST'])
def apply_job():
    # Get job URL from the request
    data = request.json
    job_url = data.get('job_url')

    if not job_url:
        return jsonify({"error": "Job URL is required"}), 400

    # Configure Selenium
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(job_url)
        time.sleep(5)  # Wait for the page to load

        # Click "Apply" button
        apply_button = driver.find_element(By.CLASS_NAME, "apply-button")
        apply_button.click()
        time.sleep(2)

        # Fill out the application form
        name_field = driver.find_element(By.NAME, "name")
        name_field.send_keys("Your Name")

        # Submit the form
        submit_button = driver.find_element(By.CLASS_NAME, "submit-button")
        submit_button.click()
        time.sleep(2)

        return jsonify({"message": "Application submitted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        driver.quit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)