import os
import json
from datetime import datetime
from pathlib import Path
from PIL import Image

# Функция для создания иерархии папок
def create_save_directory(city, company_name):
    base_dir = Path("ParsedData") / city / company_name / datetime.now().strftime("%H_%M_%d.%m.%Y")
    os.makedirs(base_dir / "code", exist_ok=True)
    return base_dir

# Функция для сохранения данных
def save_parsing_results(save_dir, city, company_name, html, screenshot_data, cms, language, framework, external_js, social_links):
    # Сохранение HTML
    html_file_path = save_dir / "code" / f"{company_name}.html"
    with open(html_file_path, 'w', encoding='utf-8') as f:
        f.write(html)

    # Сохранение скриншота
    screenshot_file_path = save_dir / f"{company_name}_screenshot.png"
    screenshot = Image.open(screenshot_data)
    screenshot.save(screenshot_file_path, format='PNG')

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