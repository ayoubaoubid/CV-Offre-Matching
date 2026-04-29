from __future__ import annotations

import argparse
import csv
import re
import sys
import time
import unicodedata
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag


BASE_URL = "https://www.marocannonces.com/"
START_URL = urljoin(BASE_URL, "categorie/309/Emploi/Offres-emploi.html")
DEFAULT_OUTPUT = "marocannonces_offres_emploi.csv"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )
}
REQUEST_TIMEOUT = 30
OUTPUT_FIELDS = [
    "Titre du poste",
    "Entreprise",
    "Secteur d'activite",
    "Localisation geographique",
    "Competences requises",
    "Niveau d'experience requis",
    "Type de contrat",
    "Date de publication",
    "URL source de l'offre",
]


def clean_text(value: str | None) -> str:
    """Nettoie les espaces, retours ligne et tabulations."""
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def normalize_for_match(value: str) -> str:
    """Supprime les accents pour faciliter les comparaisons."""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    return clean_text(ascii_only).lower()


def clean_extracted_value(value: str) -> str:
    """Nettoie les fragments extraits depuis la description."""
    plain_text = BeautifulSoup(value, "html.parser").get_text(" ", strip=True)
    cleaned = clean_text(plain_text).strip("* ")
    return "" if cleaned == "*" else cleaned


def build_page_url(page_number: int) -> str:
    """Construit l'URL de pagination."""
    if page_number <= 1:
        return START_URL
    return urljoin(BASE_URL, f"categorie/309/Emploi/Offres-emploi/{page_number}.html")


def fetch_soup(url: str, session: requests.Session) -> BeautifulSoup:
    """Telecharge une page puis la convertit en BeautifulSoup."""
    response = session.get(url, timeout=REQUEST_TIMEOUT, headers=HEADERS)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def extract_field_text(block: Tag | None, label_to_remove: str) -> str:
    """Extrait le texte utile d'un bloc en supprimant son libelle."""
    if block is None:
        return ""

    label = block.find("span")
    text = clean_text(block.get_text(" ", strip=True))
    if label is not None:
        label_text = clean_text(label.get_text(" ", strip=True))
        return clean_text(text.replace(label_text, "", 1))

    return clean_text(text.replace(label_to_remove, "", 1))


def extract_contract_type(container: Tag | None) -> str:
    """Extrait le type de contrat depuis le bloc de liste si disponible."""
    if container is None:
        return ""

    for class_name in ("contrat", "typecontrat", "type-contrat", "contract"):
        block = container.find("div", class_=class_name)
        if block is not None:
            return extract_field_text(block, "Type de contrat:")

    for block in container.find_all("div"):
        text = clean_text(block.get_text(" ", strip=True)).lower()
        if text.startswith("type de contrat") or text.startswith("contrat"):
            return extract_field_text(block, "Type de contrat:")

    return ""


def extract_time_info(container: Tag) -> tuple[str, str]:
    """Recupere le libelle de date et l'heure depuis la page liste."""
    time_block = container.find("div", class_="time")
    if time_block is None:
        return "", ""

    spans = time_block.select("em.date span")
    if not spans:
        return clean_text(time_block.get_text(" ", strip=True)), ""

    date_label = clean_text(spans[0].get_text(" ", strip=True))
    hour_label = clean_text(spans[1].get_text(" ", strip=True)) if len(spans) > 1 else ""
    return date_label, hour_label


def split_label_value(text: str) -> tuple[str, str] | None:
    """Decoupe un texte du type 'Libelle : valeur'."""
    normalized = clean_text(text)
    if ":" not in normalized:
        return None

    label, value = normalized.split(":", 1)
    label = normalize_for_match(label)
    value = clean_text(value)
    if not label or not value:
        return None

    return label, value


def extract_key_values(container: Tag | None) -> dict[str, str]:
    """Extrait les paires cle/valeur du bloc de parametres."""
    if container is None:
        return {}

    fields: dict[str, str] = {}
    for candidate in container.find_all(["li", "div", "p"]):
        parsed = split_label_value(candidate.get_text(" ", strip=True))
        if parsed is None:
            continue
        label, value = parsed
        fields[label] = value
    return fields


def extract_description_text(soup: BeautifulSoup) -> str:
    """Recupere le texte principal de l'annonce."""
    description_block = (
        soup.select_one("div.description.desccatemploi div.block")
        or soup.select_one("div.description.desccatemploi")
        or soup.select_one("div.used-cars")
    )
    if description_block is None:
        return ""
    return clean_text(description_block.get_text(" ", strip=True))


def extract_publication_date(soup: BeautifulSoup) -> str:
    """Extrait la date de publication visible sur la fiche detail."""
    for item in soup.select("li, div, span"):
        text = clean_text(item.get_text(" ", strip=True))
        if normalize_for_match(text).startswith("publiee le"):
            return clean_text(text.split(":", 1)[1] if ":" in text else text)
    return ""


def extract_company_name(description: str, fallback: str) -> str:
    """Essaie d'identifier le nom de l'entreprise."""
    if fallback and normalize_for_match(fallback) != "confidentiel":
        return fallback

    patterns = [
        r"\b([A-Z][A-Z0-9&'(). -]{1,})\s+recherche\b",
        r"\b([A-Z][A-Z0-9&'(). -]{1,})\s+recrute\b",
        r"\b([A-Z][A-Z0-9&'(). -]{1,})\s+cherche\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, description)
        if match:
            return clean_text(match.group(1))
    return fallback


def extract_sector(description: str, fields: dict[str, str]) -> str:
    """Determine le secteur d'activite."""
    for key in ("secteur", "domaine"):
        value = fields.get(key, "")
        if value:
            return value

    normalized = normalize_for_match(description)
    patterns = [
        r"secteur\s+([a-z0-9/&'() -]{3,80})",
        r"secteurs?\s+d[' ]activite\s*[:\-]?\s*([a-z0-9/&'() ,.-]{3,120})",
    ]
    for pattern in patterns:
        match = re.search(pattern, normalized, re.IGNORECASE)
        if match:
            value = clean_text(match.group(1))
            value = re.split(
                r"(mission principale|profil recherche|missions|experience|competences)",
                value,
                flags=re.IGNORECASE,
            )[0]
            return clean_text(value.rstrip(" ,.;:-"))
    return ""


def extract_labeled_segment(description: str, labels: list[str]) -> str:
    """Extrait le texte qui suit un libelle jusqu'au prochain bloc logique."""
    normalized = normalize_for_match(description)
    escaped_labels = [re.escape(label) for label in labels]
    pattern = (
        r"(?i)(?:"
        + "|".join(escaped_labels)
        + r")\s*[:\-]?\s*(.+?)(?=(?:"
        + r"profil recherche|missions?|mission principale|competences?(?: techniques)?|"
        + r"hard skills|soft skills|formation|niveau d[' ]etudes|domaine|fonction|contrat|"
        + r"entreprise|ville|salaire|$))"
    )
    match = re.search(pattern, normalized)
    if not match:
        return ""
    return clean_extracted_value(match.group(1).rstrip(" ,;:-"))


def extract_skills(description: str) -> str:
    """Recupere les competences requises ou le profil recherche."""
    skills = extract_labeled_segment(
        description,
        ["competences techniques", "competences", "hard skills", "soft skills"],
    )
    if skills:
        return skills

    profile = extract_labeled_segment(description, ["profil recherche"])
    if profile:
        return profile

    return ""


def extract_experience(description: str, fields: dict[str, str]) -> str:
    """Recupere le niveau d'experience requis."""
    value = fields.get("experience", "")
    if value:
        return value

    experience = extract_labeled_segment(description, ["experience"])
    if experience:
        return experience

    match = re.search(
        r"((?:minimum\s+)?\d+\s*(?:a|an|ans)\b[^.]{0,120})",
        normalize_for_match(description),
        re.IGNORECASE,
    )
    if match:
        return clean_text(match.group(1))

    return ""


def build_output_row(
    title: str,
    location: str,
    contract_type: str,
    publication_date: str,
    url: str,
    company: str,
    sector: str,
    skills: str,
    experience: str,
) -> dict[str, str]:
    """Construit la ligne finale ecrite dans le CSV."""
    return {
        "Titre du poste": title,
        "Entreprise": company,
        "Secteur d'activite": sector,
        "Localisation geographique": location,
        "Competences requises": skills,
        "Niveau d'experience requis": experience,
        "Type de contrat": contract_type,
        "Date de publication": publication_date,
        "URL source de l'offre": url,
    }


def fetch_offer_details(url: str, session: requests.Session) -> dict[str, str]:
    """Enrichit une annonce avec les donnees de sa fiche detail."""
    soup = fetch_soup(url, session)
    detail_fields = extract_key_values(soup.select_one("div.parameter"))
    description = extract_description_text(soup)
    publication_date = extract_publication_date(soup)

    return {
        "company": extract_company_name(description, detail_fields.get("entreprise", "")),
        "sector": extract_sector(description, detail_fields),
        "skills": extract_skills(description),
        "experience": extract_experience(description, detail_fields),
        "publication_date": publication_date,
        "contract_type": detail_fields.get("contrat", ""),
        "location": detail_fields.get("ville", ""),
    }


def parse_listing(container: Tag, session: requests.Session) -> dict[str, str] | None:
    """Transforme un bloc HTML d'annonce en ligne prete pour le CSV."""
    link = container.find("a", href=lambda href: href and "/annonce/" in href)
    if link is None:
        return None

    holder = link.find("div", class_="holder") or link
    title = clean_text((holder.find("h3") or link).get_text(" ", strip=True))

    city_tag = holder.find("span", class_="location")
    city = clean_text(city_tag.get_text(" ", strip=True)) if city_tag else ""

    relative_url = link.get("href", "")
    full_url = urljoin(BASE_URL, relative_url)
    details = fetch_offer_details(full_url, session)

    location = details["location"] or city
    contract_type = details["contract_type"] or extract_contract_type(holder)
    publication_date = details["publication_date"]
    if not publication_date:
        published_day, published_time = extract_time_info(container)
        publication_date = clean_text(
            " ".join(part for part in (published_day, published_time) if part)
        )

    return build_output_row(
        title=title,
        location=location,
        contract_type=contract_type,
        publication_date=publication_date,
        url=full_url,
        company=details["company"],
        sector=details["sector"],
        skills=details["skills"],
        experience=details["experience"],
    )


def scrape_page(page_number: int, session: requests.Session) -> list[dict[str, str]]:
    """Scrape une page de resultats."""
    url = build_page_url(page_number)
    soup = fetch_soup(url, session)
    rows: list[dict[str, str]] = []

    premium_blocks = soup.select("div.listing_set.list article.listing")
    standard_blocks = soup.select("ul.cars-list > li")

    for block in premium_blocks:
        row = parse_listing(block, session)
        if row:
            rows.append(row)

    for block in standard_blocks:
        row = parse_listing(block, session)
        if row:
            rows.append(row)

    return rows


def deduplicate(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    """Supprime les doublons sur l'URL source."""
    seen_urls: set[str] = set()
    unique_rows: list[dict[str, str]] = []

    for row in rows:
        url = row["URL source de l'offre"]
        if url in seen_urls:
            continue
        seen_urls.add(url)
        unique_rows.append(row)

    return unique_rows


def save_to_csv(rows: list[dict[str, str]], output_path: Path) -> None:
    """Enregistre les resultats dans un CSV compatible Excel."""
    if not rows:
        print("Aucune annonce n'a ete extraite.")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def scrape_offers(max_pages: int, delay_seconds: float) -> list[dict[str, str]]:
    """Scrape plusieurs pages d'offres d'emploi."""
    all_rows: list[dict[str, str]] = []

    with requests.Session() as session:
        for page_number in range(1, max_pages + 1):
            print(f"[INFO] Scraping page {page_number}/{max_pages}...")
            page_rows = scrape_page(page_number, session)
            print(f"[INFO] {len(page_rows)} annonces trouvees sur la page {page_number}.")
            all_rows.extend(page_rows)

            if page_number < max_pages:
                time.sleep(delay_seconds)

    return deduplicate(all_rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scraper les offres d'emploi de MarocAnnonces avec BeautifulSoup."
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=1,
        help="Nombre de pages a scraper (1 par defaut).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Pause en secondes entre deux pages (2.0 par defaut).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=DEFAULT_OUTPUT,
        help="Nom du fichier CSV de sortie.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.pages < 1:
        print("[ERREUR] --pages doit etre superieur ou egal a 1.")
        return 1

    output_path = Path(__file__).resolve().parent / args.output

    try:
        rows = scrape_offers(max_pages=args.pages, delay_seconds=args.delay)
        save_to_csv(rows, output_path)
    except requests.RequestException as exc:
        print(f"[ERREUR] Probleme reseau pendant le scraping: {exc}")
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"[ERREUR] Probleme inattendu: {exc}")
        return 1

    print(f"[OK] {len(rows)} annonces sauvegardees dans: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
