import os
import json
from datetime import date, datetime
from pathlib import Path
# from PIL import Image


def get_html(company_name, save_dir):
    html_file_path = save_dir / f"{company_name}.html"
    if os.path.isfile(html_file_path):
        with open(html_file_path) as f:
            s = f.read()
        return s
    else:
        return False


def _folder_name_for_date(when: datetime) -> str:
    return when.strftime("%d.%m.%Y")


def save_directory_for_date(industry: str, city: str, company_name: str, when: datetime) -> Path:
    """Path to ParsedData/.../dd.mm.yyyy (does not create the directory)."""
    return Path("ParsedData") / industry / city / company_name / _folder_name_for_date(when)


def save_directory_for_parse_date(
    industry: str, city: str, company_name: str, parse_date: date
) -> Path:
    """Path to ParsedData/.../dd.mm.yyyy for a calendar date (folder may or may not exist)."""
    return (
        Path("ParsedData")
        / industry
        / city
        / company_name
        / parse_date.strftime("%d.%m.%Y")
    )


# Функция для создания иерархии папок
def create_save_directory(industry, city, company_name):
    base_dir = save_directory_for_date(industry, city, company_name, datetime.now())
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def remove_empty_directory(directory_path):
    try:
        os.removedirs(directory_path)
        print(f"Директория {directory_path} успешно удалена.")
    except OSError as e:
        print(f"Ошибка при удалении директории {directory_path}: {e}")


# Функция для сохранения данных
def save_parsing_results(save_dir, city, company_name, html, screenshot_data, cms, language, framework, external_js, social_links):
    # Сохранение HTML
    html_file_path = save_dir / f"{company_name}.html"
    with open(html_file_path, 'w', encoding='utf-8') as f:
        f.write(html)

    # Сохранение JSON с информацией
    data = {
        'cms': cms,
        'language': language,
        'framework': framework,
        'external_js': external_js,
        'social_links': social_links
    }

    json_file_path = save_dir / f"{company_name}.json"
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)

    print(f"Данные по компании {company_name} успешно сохранены.")
