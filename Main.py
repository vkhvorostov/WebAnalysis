import csv
from datetime import date
from typing import Optional, Tuple

import HtmlParser
import DeepCodeAnalyser
import JSAnalyser
import ScreenshotMaker
import SimpleSaver
from DomainWhois import get_domain_created_date
from SqlORM import Company, CompanyData, PostgresDB


def _as_text(value) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)


def process(
    db: PostgresDB,
    company: Company,
    parse_date: Optional[date] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Analyze HTML for a company. If parse_date is set, load HTML from ParsedData/.../dd.mm.yyyy
    and do not fetch from the internet. If parse_date is None, use today's folder and fetch from the net when needed.

    Returns (success, error_message).
    """
    company_name = company.company_name.replace("/", "-")

    if parse_date is not None:
        save_dir = SimpleSaver.save_directory_for_parse_date(
            company.industry, company.city, company_name, parse_date
        )
        if not save_dir.is_dir():
            return False, f"ParsedData folder not found: {save_dir}"
        screenshot_save_path = save_dir / f"{company_name}_screenshot.png"
        html = SimpleSaver.get_html(company_name, save_dir)
        if not html:
            return False, f"No {company_name}.html under {save_dir}"

        data = SimpleSaver.get_json(company_name, save_dir)
        if not data:
            return False, f"No {company_name}.json under {save_dir}"
        cms = data.get("cms", "Unknown")
        language = data.get("language", "Unknown")
        framework = data.get("framework", "Unknown")
        external_js = data.get("external_js", [])
        social_links = data.get("social_links", [])
   
    else:
        save_dir = SimpleSaver.create_save_directory(
            company.industry, company.city, company_name
        )
        screenshot_save_path = save_dir / f"{company_name}_screenshot.png"
        headers = {}

        html, headers = HtmlParser.get_html(company.url)
        if not html:
            print(f"Не удалось получить HTML для {company_name}.")
            SimpleSaver.remove_empty_directory(save_dir)
            return False, "Failed to fetch HTML"
        html = ScreenshotMaker.take_screenshot(company.url, screenshot_save_path)
        if not html:
            print(f"Не удалось сделать скриншот для {company_name}.")
            SimpleSaver.remove_empty_directory(save_dir)
            return False, "Failed to capture screenshot"

        cms = DeepCodeAnalyser.detect_cms(html)
        language = DeepCodeAnalyser.detect_language(headers)
        framework = DeepCodeAnalyser.detect_framework(headers)
        external_js = JSAnalyser.find_external_js(html)
        social_links = JSAnalyser.find_social_links(html)

        SimpleSaver.save_parsing_results(
            save_dir=save_dir,
            company_name=company_name,
            html=html,
            cms=cms,
            language=language,
            framework=framework,
            external_js=external_js,
            social_links=social_links,
        )

    domain_created = get_domain_created_date(company.url)

    effective_date = parse_date or date.today()
    if parse_date is not None:
        # Re-parse from disk should overwrite same-date snapshot for the company.
        existing = (
            db.session.query(CompanyData)
            .filter(
                CompanyData.company_id == company.id,
                CompanyData.date_parse == effective_date,
            )
            .first()
        )
        if existing:
            existing.cms = _as_text(cms)
            existing.language = _as_text(language)
            existing.framework = _as_text(framework)
            existing.external_js = _as_text(external_js)
            existing.social_links = _as_text(social_links)
            existing.domain_created = domain_created
        else:
            db.session.add(
                CompanyData(
                    company_id=company.id,
                    date_parse=effective_date,
                    cms=_as_text(cms),
                    language=_as_text(language),
                    framework=_as_text(framework),
                    external_js=_as_text(external_js),
                    social_links=_as_text(social_links),
                    domain_created=domain_created,
                )
            )
    else:
        # Live parse always appends a new historical row.
        db.session.add(
            CompanyData(
                company_id=company.id,
                date_parse=effective_date,
                cms=_as_text(cms),
                language=_as_text(language),
                framework=_as_text(framework),
                external_js=_as_text(external_js),
                social_links=_as_text(social_links),
                domain_created=domain_created,
            )
        )
    db.session.commit()


    return True, None


def main():
    input_file = "companies.csv"
    db = PostgresDB(db_name="webanalysis", user="exampleuser", password="examplepwd")
    with open(input_file, "r", newline="") as in_file:
        csv_reader = csv.DictReader(in_file, delimiter=";")
        for row in csv_reader:
            city = row["city"].strip()
            industry = row["industry"].strip()
            company_name = row["company_name"].strip().replace("/", "-")
            already_saved = db.get_company(city, industry, company_name)
            if already_saved:
                company_obj = db.get_company_by_id(already_saved[0])
            else:
                company_obj = db.set(
                    "companies", (company_name, city, industry, row["url"].strip())
                )
            if company_obj:
                process(db, company_obj, parse_date=None)
    db.close()


if __name__ == "__main__":
    main()
