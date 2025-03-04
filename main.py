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
import re
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
    resultat = "<h1>Scrapping offre linkedin</h1>"
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

    driver.get("https://www.linkedin.com/login")

    # Connexion à LinkedIn
    email = driver.find_element(By.ID, "username")
    email.send_keys("thierry.richol@gmail.com")
    password = driver.find_element(By.ID, "password")
    password.send_keys("Taitai44!")
    password.send_keys(Keys.RETURN)
    
    resultat += "<ul>"

    max_request = 2
    iLoop = 0

    # Attente de chargement
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "global-nav-typeahead")))

    # Recherche des offres
    # mots_cles = ["Automatisation", "IoT", "Cloud Computing", "Full-stack Web", "Full-stack Mobile", "Chef de projet IT"]
    url_list_job = "https://www.linkedin.com/jobs/search/?alertAction=viewjobs&currentJobId=4173007979&f_E=3%2C4%2C5%2C6&f_TPR=r86400&f_WT=3%2C2&geoId=105015875&keywords=Freelance&location=France&origin=JOB_SEARCH_PAGE_JOB_FILTER"
    offres = []   

    driver.get(url_list_job)

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "job-card-container")))
    time.sleep(4)  # Pause pour éviter les blocages

    job_cards = driver.find_elements(By.CSS_SELECTOR, "li.occludable-update")

    offres = []

    for card in job_cards:
        if iLoop == max_request:
            break  # Sort de la boucle après 6 itérations
        iLoop += 1
        try:
            # Extraction du titre du poste
            title_element = card.find_element(By.CSS_SELECTOR, "a[href*='/jobs/view/']")
            print("\n\n----------------------")
            title = title_element.get_attribute("aria-label") or title_element.text.strip()
            print("title:", title)
            
            # Extraction du nom de l'entreprise
            company = card.find_element(By.CSS_SELECTOR, ".artdeco-entity-lockup__subtitle").text.strip()
            print("entreprise:", company)
            
            # Extraction de la localisation
            localisation = card.find_element(By.CSS_SELECTOR, ".job-card-container__metadata-wrapper li").text.strip()
            print("localisation:", localisation)
            
            # Extraction du lien pour postuler (lien vers la page de détail)
            lien = title_element.get_attribute("href")
            print("lien:", lien)

            card.click()
            # Descriptif
            description = ""
            contact_email = ""
            apply_method = "unknown"
            try:
                description_panel = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-description__container"))
                )
                about = description_panel.find_element(By.CSS_SELECTOR, ".mt4").text.strip()
                detail = description_panel.find_element(By.CSS_SELECTOR, ".jobs-description__details").text.strip()
                description = about + "\n" + detail

                # Expression régulière pour extraire les emails
                pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
                emails = re.findall(pattern, description)
                # Retourner le premier email trouvé s'il existe, sinon une chaîne vide
                contact_email = emails[0] if emails else ""

                print("Email(s) extrait(s) :", contact_email)

            except:
                description = "Non disponible"
            print("description:", description)

            # Competences
            competences = ""
            try:
                competences_panel = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".job-details-how-you-match__skills-section-descriptive-skill"))
                )
                competences = competences_panel.text.strip()
            except:
                competences = "Non disponible"
            print("competences:", competences)            

            # url_postulation
            link_postuler = ""
            try:
                button_postuler_card = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-apply-button--top-card"))
                )
                button_postuler = button_postuler_card.find_element(By.CSS_SELECTOR, "button.jobs-apply-button")


                # Vérifier si l'attribut "data-job-id" est présent
                if button_postuler.get_attribute("data-job-id"):
                    print("L'attribut data-job-id est présent sur ce bouton.")
                    apply_method = "easy_apply"
                else:
                    button_postuler.click()
                    print("Le bouton a été cliqué.")
                    # Stocker l'identifiant de la fenêtre d'origine
                    original_window = driver.current_window_handle

                    # Attendre que la nouvelle fenêtre s'ouvre (par exemple, attendre 2 fenêtres)
                    WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))

                    # Basculer vers la nouvelle fenêtre
                    for handle in driver.window_handles:
                        if handle != original_window:
                            driver.switch_to.window(handle)
                            break

                    # Récupérer l'URL de la nouvelle page
                    link_postuler = driver.current_url
                    print("URL de la page ouverte :", link_postuler)

                    # Fermer la nouvelle fenêtre
                    driver.close()
                    apply_method = "email" if contact_email else "postuler"

            except Exception as e:
                link_postuler = "Non disponible"
                print("Erreur link_postuler:", e)
            
            print("link_postuler:", link_postuler)
            
            
            # Pause rapide pour éviter les surcharges de clics
        except Exception as e:
            print("Erreur lors de l'extraction d'une job card:", e)
    
    

        offres.append({
            "id": iLoop,
            "title": title,
            "company": company,
            "location": localisation,
            "job_url": lien,
            "date_scraped": datetime.now().strftime("%Y-%m-%d"),
            "keywords_matched": competences,
            "apply_method": apply_method,
            "contact_email": contact_email,
            "description": description,
            "lien_postuler": link_postuler,
            "source": "linkedin"
        })


    time.sleep(2)  # Pause pour éviter les blocages
    with open("offres.json", "w", encoding="utf-8") as f:
        json.dump(offres, f)

    # Envoi des données au Webhook de Make
    webhook_url = "https://hook.eu2.make.com/k44d4ig9ragse9f9ovb22vh1ffj16bu3"  # Remplacez par l’URL de votre Webhook
    headers = {"Content-Type": "application/json"}
    response = requests.post(webhook_url, json=offres, headers=headers)

    if response.status_code == 200:
        resultat += "<li>Données envoyées avec succès à Make"
    else:
        resultat += "<li>Erreur lors de l’envoi : {response.status_code} - {response.text}"

    resultat += "</ul>"
    resultat += "<h1>FIN</h1>"
    driver.quit()
    return resultat

@app.route('/hello', methods=['GET'])
def hello():
    return "Hello Worlds"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)