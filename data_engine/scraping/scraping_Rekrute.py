
#Scraper Rekrute.com - Production Complet/


import time
import random
import pandas as pd
import os
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

BASE_URL = 'https://www.rekrute.com'
CSV_FILE = f'rekrute_jobs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

def setup_driver():
    """Configure Selenium Webdriver."""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def extract_job_links_from_page(driver):
    """Extrait les liens des offres depuis la page liste."""
    try:
        soup = BeautifulSoup(driver.page_source, 'lxml')
        jobs = soup.find_all('li', class_='post-id')  # LI not DIV!
        
        links = []
        for job in jobs:
            try:
                link_tag = job.find('a')
                if link_tag:
                    href = link_tag.get('href', '')
                    link = BASE_URL + href if href.startswith('/') else href
                    if link and link not in links:
                        links.append(link)
            except:
                pass
        
        return links
    except Exception as e:
        return []

def scrape_job_detail(driver, link):
    """Scrape complètement une page d'offre d'emploi."""
    try:
        driver.get(link)
        time.sleep(0.8)
        
        soup = BeautifulSoup(driver.page_source, 'lxml')
        
        job_data = {
            'titre': None,
            'entreprise': None,
            'localisation': None,
            'contrat': None,
            'secteur': None,
            'experience': None,
            'formation': None,
            'date_publication': None,
            'description': None,
            'lien': link,
        }
        
        # ==================== TITRE ====================
        h2 = soup.find('h2')
        if h2:
            titre = h2.get_text(strip=True)
            if '|' in titre:
                job_data['titre'] = titre.split('|')[0].strip()
                job_data['localisation'] = titre.split('|')[1].strip()
            else:
                job_data['titre'] = titre
        
        # ==================== ENTREPRISE, SECTEUR ====================
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = p.get_text(separator=' ', strip=True)
            
            if 'Entreprise:' in text:
                job_data['entreprise'] = text.replace('Entreprise:', '').strip()
            
            if 'Secteur:' in text or 'Secteur d\'activité' in text:
                secteur_text = text.replace('Secteur:', '').replace('Secteur d\'activité:', '').strip()
                if secteur_text:
                    job_data['secteur'] = secteur_text
        
        # ==================== DESCRIPTION ====================
        for div in soup.find_all('div', class_=True):
            classes = str(div.get('class', []))
            if any(x in classes.lower() for x in ['content', 'description', 'body']):
                text = div.get_text(separator=' ', strip=True)
                if len(text) > 150:
                    job_data['description'] = text[:1200]
                    break
        
        # ==================== CONTRAT, EXPÉRIENCE, FORMATION ====================
        list_items = soup.find_all('li')
        for li in list_items:
            li_text = li.get_text(separator=' ', strip=True)
            
            # Contrat
            for ct in ['CDI', 'CDD', 'STAGE', 'FREELANCE', 'INTERIM', 'ALTERNANCE']:
                if ct in li_text.upper() and not job_data['contrat']:
                    job_data['contrat'] = ct
                    break
            
            # Expérience
            if ('Expérience' in li_text or 'Experience' in li_text) and not job_data['experience']:
                job_data['experience'] = li_text.replace('Expérience', '').replace('Experience', '').replace('Exp.', '').strip()[:250]
            
            # Formation
            if ('Formation' in li_text or 'Diplôme' in li_text or 'Bac ' in li_text) and not job_data['formation']:
                job_data['formation'] = li_text.replace('Formation', '').replace('Diplôme', '').strip()[:250]
        
        # ==================== DATE ====================
        for span in soup.find_all('span'):
            span_text = span.get_text(strip=True)
            if any(c.isdigit() for c in span_text) and len(span_text) < 15 and not job_data['date_publication']:
                if '/' in span_text or 'jour' in span_text.lower() or 'mois' in span_text.lower():
                    job_data['date_publication'] = span_text
                    break
        
        return job_data
        
    except Exception as e:
        return None

def scrape_all_pages(driver, max_pages=200):
    """Scrape toutes les pages et enrichit les données."""
    all_jobs = []
    processed_links = set()
    
    for page in range(1, max_pages + 1):
        url = f'{BASE_URL}/offres.html?p={page}'
        
        try:
            driver.get(url)
            time.sleep(5 + random.uniform(0, 2))
            
            # Attendre que les offres se chargent
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, 'post-id'))
                )
            except:
                pass
            
            # Extraire les liens
            links = extract_job_links_from_page(driver)
            
            if not links:
                print(f'  ⛔ Aucune offre trouvée — fin du scraping.')
                break
            
            # Scraper chaque offre
            for i, link in enumerate(links, 1):
                if link in processed_links:
                    continue
                
                try:
                    job_data = scrape_job_detail(driver, link)
                    if job_data:
                        titre = (job_data['titre'][:35] if job_data['titre'] else 'N/A')
                        all_jobs.append(job_data)
                        processed_links.add(link)
                    time.sleep(random.uniform(0.3, 0.6))
                except Exception as e:
                    print(f'    [{i:2}/{len(links)}] ❌ Erreur')
                    continue
            
            print(f'  ✅ Page OK (total: {len(all_jobs)} offres)')
            time.sleep(random.uniform(1, 1.5))
            
        except Exception as e:
            print(f'  ❌ Erreur page {page}: {e}')
            break
    
    return all_jobs

def save_to_csv(jobs):
    """Sauvegarde les offres dans un CSV."""
    if not jobs:
        print('❌ Pas de données à sauvegarder')
        return 0
    
    df = pd.DataFrame(jobs)
    df.to_csv(CSV_FILE, index=False, encoding='utf-8-sig')
    
    return len(df)

def print_stats(jobs):
    """Affiche les statistiques du scraping."""
    print(f'\n\n{'='*80}')
    print('📊 STATISTIQUES FINALES')
    print('='*80)
    
    if not jobs:
        print('❌ Aucune donnée')
        return
    
    df = pd.DataFrame(jobs)
    
    print(f'\n✅ Total offres: {len(df)}')
    print(f'\n📋 Taux de remplissage par champ:')
    
    for col in df.columns:
        remplis = df[col].notna().sum()
        pct = (remplis / len(df)) * 100
        status = '✅' if pct >= 90 else '⚠️' if pct >= 50 else '❌'
        print(f'   {status} {col:20} : {remplis:3}/{len(df)} ({pct:5.1f}%)')
    
    print(f'\n📁 Fichier généré: {CSV_FILE}')
    print('='*80)

def main():
    """Fonction principale - Exécution récurrente toutes les 13 heures."""
    run_count = 0
    
    while True:
        run_count += 1
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f'\n{'='*80}')
        print(f'🚀 SCRAPER REKRUTE.COM - PRODUCTION (130 pages)')
        print(f'Exécution #{run_count} - Démarré: {now}')
        print(f'{'='*80}\n')
        
        driver = setup_driver()
        all_jobs = []
        try:
            all_jobs = scrape_all_pages(driver, max_pages=130)
        except KeyboardInterrupt:
            print('\n\n⚠️ Scraping interrompu (Ctrl+C)')
            driver.quit()
            break
        except Exception as e:
            print(f'❌ Erreur critique: {e}')
        finally:
            driver.quit()
            # Toujours sauvegarder ce qu'on a collecté
            if all_jobs:
                total = save_to_csv(all_jobs)
                print_stats(all_jobs)
            print(f'\n✅ SCRAPING TERMINÉ')
            print(f'Fichier: {CSV_FILE}\n')
        
        # Attendre 13 heures avant la prochaine exécution
        next_run = datetime.now() + timedelta(hours=13)
        print(f'⏰ Prochain scraping: {next_run.strftime("%Y-%m-%d %H:%M:%S")}')
        print(f'⏳ En attente de 13 heures...\n')
        time.sleep(13 * 3600)  # 13 heures en secondes

if __name__ == '__main__':
    main()
