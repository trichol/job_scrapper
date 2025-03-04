from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import platform
import requests
from datetime import datetime

app = Flask(__name__)

@app.route('/repondre_linkedin', methods=['POST'])
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

@app.route('/scrapp_linkedin', methods=['GET'])
def scrapp():
    # Configuration du WebDriver
    # Specify the path to the ChromeDriver executable
    os_name = platform.system()
    chrome_driver_path = "E:\\WORK\\PROJETS\\WORKSPACE\\job_scrapper\\CHROME_DRIVER\\chromedriver.exe"
    if os_name == "Windows":
        print("Le système d'exploitation est Windows.")
    elif os_name == "Linux":
        print("Le système d'exploitation est Linux.")
        chrome_driver_path = "/usr/bin/chromedriver"
    else:
        print("Système d'exploitation inconnu :", os_name)
        return "Système d'exploitation inconnu :" + os_name
    

    # Use the Service class to set the executable path
    service = Service(chrome_driver_path)

    # Initialize the WebDriver with the Service object
    driver = webdriver.Chrome(service=service)

    # driver = webdriver.Chrome(executable_path="E:\\WORK\\PROJETS\\WORKSPACE\\job_scrapper\\CHROME_DRIVER\\chromedriver")
    driver.get("https://www.linkedin.com/login")

    # Connexion à LinkedIn
    email = driver.find_element(By.ID, "username")
    email.send_keys("thierry.richol@gmail.com")
    password = driver.find_element(By.ID, "password")
    password.send_keys("Taitai44!")
    password.send_keys(Keys.RETURN)
    max_request = 1

    # Attente de chargement
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "global-nav-typeahead")))

    # Recherche des offres
    mots_cles = ["Automatisation", "IoT", "Cloud Computing", "Full-stack Web", "Full-stack Mobile", "Gestion de projet IT"]
    offres = []

    for mot_cle in mots_cles:
        driver.get("https://www.linkedin.com/jobs/")
        search_box = driver.find_element(By.CLASS_NAME, "jobs-search-box__text-input")
        search_box.clear()
        search_box.send_keys(f"{mot_cle} France")
        search_box.send_keys(Keys.RETURN)
        
        # Attendre les résultats
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "job-card-container")))
        
        # Récupérer les offres (limité à max_request par mot-clé pour cet exemple)
        jobs = driver.find_elements(By.CLASS_NAME, "job-card-container")[:max_request]
        for job in jobs:
            titre = job.find_element(By.CLASS_NAME, "job-card-list__title--link").text
            entreprise = job.find_element(By.CLASS_NAME, "job-card-container__company-name").text
            localisation = job.find_element(By.CLASS_NAME, "job-card-container__metadata-item").text
            lien = job.find_element(By.TAG_NAME, "a").get_attribute("href")
            
            # Visiter la page de l’offre pour plus de détails
            driver.get(lien)
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "jobs-description")))
            description = driver.find_element(By.CLASS_NAME, "jobs-description").text[:200]  # Limite à 200 caractères
            
            # Détection de la méthode de candidature
            apply_method = "unknown"
            contact_email = None
            if "Easy Apply" in driver.page_source:
                apply_method = "easy_apply"
            elif "@" in description:  # Recherche basique d’un email
                # À affiner avec regex si besoin
                contact_email = [word for word in description.split() if "@" in word][0] if "@" in description else None
                apply_method = "email" if contact_email else "unknown"
            
            offres.append({
                "title": titre,
                "company": entreprise,
                "location": localisation,
                "job_url": lien,
                "date_scraped": datetime.now().strftime("%Y-%m-%d"),
                "keywords_matched": [mot_cle],
                "apply_method": apply_method,
                "contact_email": contact_email,
                "description": description
            })
            
            
            # offres.append({"titre": titre, "entreprise": entreprise, "localisation": localisation, "lien": lien})
        
        time.sleep(2)  # Pause pour éviter les blocages

    # Sauvegarde temporaire (sera envoyée à Make)
    import json
    with open("offres.json", "w", encoding="utf-8") as f:
        json.dump(offres, f)

    driver.quit()

    # Envoi des données au Webhook de Make
    webhook_url = "https://hook.eu2.make.com/k44d4ig9ragse9f9ovb22vh1ffj16bu3"  # Remplacez par l’URL de votre Webhook
    headers = {"Content-Type": "application/json"}
    response = requests.post(webhook_url, json=offres, headers=headers)

    if response.status_code == 200:
        print("Données envoyées avec succès à Make")
    else:
        print(f"Erreur lors de l’envoi : {response.status_code} - {response.text}")

@app.route('/hello', methods=['GET'])
def hello():
    return "Hello Worlds"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)