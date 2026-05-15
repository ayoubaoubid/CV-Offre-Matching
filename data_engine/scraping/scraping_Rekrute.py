# Scraper Rekrute.com.
#
# Par defaut, le script fait une seule execution puis s'arrete. C'est important
# pour que la pipeline globale puisse continuer vers le preprocessing et l'import
# Django. Pour une execution recurrente, utiliser --loop --interval-hours 8.

from __future__ import annotations

import argparse
import random
import time
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


BASE_URL = "https://www.rekrute.com"
SCRIPT_DIR = Path(__file__).resolve().parent
LATEST_CSV = SCRIPT_DIR / "rekrute_jobs_.csv"


def normalize_for_match(value):
    text = str(value or "")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return text.lower()


def value_after_colon(value):
    text = str(value or "").strip()
    if ":" in text:
        return text.split(":", 1)[1].strip()
    return text


def setup_driver():
    """Configure Selenium WebDriver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


def extract_job_links_from_page(driver):
    """Extrait les liens des offres depuis une page liste Rekrute."""
    soup = BeautifulSoup(driver.page_source, "lxml")
    jobs = soup.find_all("li", class_="post-id")

    links = []
    for job in jobs:
        link_tag = job.find("a")
        if not link_tag:
            continue

        href = link_tag.get("href", "")
        link = BASE_URL + href if href.startswith("/") else href
        if link and link not in links:
            links.append(link)

    return links


def scrape_job_detail(driver, link):
    """Scrape une page detail d'offre d'emploi."""
    try:
        driver.get(link)
        time.sleep(0.8)

        soup = BeautifulSoup(driver.page_source, "lxml")

        job_data = {
            "titre": None,
            "entreprise": None,
            "localisation": None,
            "contrat": None,
            "secteur": None,
            "experience": None,
            "formation": None,
            "date_publication": None,
            "description": None,
            "lien": link,
        }

        h2 = soup.find("h2")
        if h2:
            title_text = h2.get_text(strip=True)
            if "|" in title_text:
                title, location = title_text.split("|", 1)
                job_data["titre"] = title.strip()
                job_data["localisation"] = location.strip()
            else:
                job_data["titre"] = title_text

        for paragraph in soup.find_all("p"):
            text = paragraph.get_text(separator=" ", strip=True)
            normalized_text = normalize_for_match(text)

            if "entreprise" in normalized_text and ":" in text:
                job_data["entreprise"] = value_after_colon(text)

            if "secteur:" in normalized_text or "secteur d'activite" in normalized_text:
                sector_text = value_after_colon(text)
                if sector_text:
                    job_data["secteur"] = sector_text

        for div in soup.find_all("div", class_=True):
            classes = str(div.get("class", [])).lower()
            if any(name in classes for name in ["content", "description", "body"]):
                text = div.get_text(separator=" ", strip=True)
                if len(text) > 150:
                    job_data["description"] = text[:1200]
                    break

        for item in soup.find_all("li"):
            item_text = item.get_text(separator=" ", strip=True)
            normalized_item = normalize_for_match(item_text)
            upper_text = item_text.upper()

            for contract_type in [
                "CDI",
                "CDD",
                "STAGE",
                "FREELANCE",
                "INTERIM",
                "ALTERNANCE",
            ]:
                if contract_type in upper_text and not job_data["contrat"]:
                    job_data["contrat"] = contract_type
                    break

            if "experience" in normalized_item and not job_data["experience"]:
                job_data["experience"] = (
                    item_text.replace("Experience", "")
                    .replace("Exp.", "")
                    .strip()[:250]
                )

            if (
                "formation" in normalized_item
                or "diplome" in normalized_item
                or "bac " in normalized_item
            ) and not job_data["formation"]:
                job_data["formation"] = (
                    item_text.replace("Formation", "")
                    .replace("Diplome", "")
                    .strip()[:250]
                )

        for span in soup.find_all("span"):
            span_text = span.get_text(strip=True)
            if any(char.isdigit() for char in span_text) and len(span_text) < 15:
                if "/" in span_text or "jour" in span_text.lower() or "mois" in span_text.lower():
                    job_data["date_publication"] = span_text
                    break

        return job_data
    except Exception as exc:
        print(f"Erreur detail offre {link}: {exc}")
        return None


def scrape_all_pages(driver, max_pages=130):
    """Scrape les pages Rekrute et enrichit les offres depuis les pages detail."""
    all_jobs = []
    processed_links = set()

    for page in range(1, max_pages + 1):
        url = f"{BASE_URL}/offres.html?p={page}"

        try:
            driver.get(url)
            time.sleep(5 + random.uniform(0, 2))

            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "post-id"))
                )
            except Exception:
                pass

            links = extract_job_links_from_page(driver)
            if not links:
                print("Aucune offre trouvee, fin du scraping.")
                break

            for index, link in enumerate(links, 1):
                if link in processed_links:
                    continue

                job_data = scrape_job_detail(driver, link)
                if job_data:
                    all_jobs.append(job_data)
                    processed_links.add(link)

                time.sleep(random.uniform(0.3, 0.6))
                print(f"  Page {page} - offre {index}/{len(links)}")

            print(f"Page {page} OK, total actuel: {len(all_jobs)} offres")
            time.sleep(random.uniform(1, 1.5))
        except Exception as exc:
            print(f"Erreur page {page}: {exc}")
            break

    return all_jobs


def save_to_csv(jobs):
    """Sauvegarde en archive timestamp et met a jour le fichier stable."""
    if not jobs:
        print("Pas de donnees a sauvegarder.")
        return 0, None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_csv = SCRIPT_DIR / f"rekrute_jobs_{timestamp}.csv"

    df = pd.DataFrame(jobs)
    df.to_csv(archive_csv, index=False, encoding="utf-8-sig")
    df.to_csv(LATEST_CSV, index=False, encoding="utf-8-sig")

    return len(df), archive_csv


def print_stats(jobs, archive_csv):
    print("\n" + "=" * 80)
    print("STATISTIQUES FINALES REKRUTE")
    print("=" * 80)

    if not jobs:
        print("Aucune donnee.")
        return

    df = pd.DataFrame(jobs)
    print(f"Total offres: {len(df)}")

    print("Taux de remplissage par champ:")
    for col in df.columns:
        filled = df[col].notna().sum()
        pct = (filled / len(df)) * 100
        print(f"  {col:20}: {filled:4}/{len(df)} ({pct:5.1f}%)")

    print(f"Archive generee: {archive_csv}")
    print(f"Fichier stable mis a jour: {LATEST_CSV}")
    print("=" * 80)


def run_once(max_pages):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("\n" + "=" * 80)
    print(f"SCRAPER REKRUTE.COM - demarre: {now}")
    print(f"Pages max: {max_pages}")
    print("=" * 80)

    driver = setup_driver()
    all_jobs = []
    try:
        all_jobs = scrape_all_pages(driver, max_pages=max_pages)
    finally:
        driver.quit()

    total, archive_csv = save_to_csv(all_jobs)
    print_stats(all_jobs, archive_csv)
    print(f"Scraping Rekrute termine: {total} offres.")
    return total


def main():
    parser = argparse.ArgumentParser(description="Scraper Rekrute.")
    parser.add_argument("--max-pages", type=int, default=130)
    parser.add_argument("--loop", action="store_true", help="Relance le scraping en boucle.")
    parser.add_argument("--interval-hours", type=float, default=8)
    args = parser.parse_args()

    while True:
        run_once(args.max_pages)

        if not args.loop:
            break

        next_run = datetime.now() + timedelta(hours=args.interval_hours)
        print(f"Prochain scraping Rekrute: {next_run:%Y-%m-%d %H:%M:%S}")
        time.sleep(args.interval_hours * 3600)


if __name__ == "__main__":
    main()
