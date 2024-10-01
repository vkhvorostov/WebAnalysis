import os
import json
from datetime import datetime
from pathlib import Path
from PIL import Image

# Функция для создания иерархии папок и сохранения данных
def save_parsing_results(city, company_name, html, screenshot_data, cms, language, framework, external_js,
                         social_links):
    # Определяем базовую директорию
    base_dir = Path("ParsedData") / city / company_name / datetime.now().strftime("%H_%M_%d.%m.%Y")
    os.makedirs(base_dir, exist_ok=True)

    # Создание папки "code" для хранения HTML, JS и CSS
    code_dir = base_dir / "code"
    os.makedirs(code_dir, exist_ok=True)

    # Сохранение HTML
    html_file_path = code_dir / f"{company_name}.html"
    with open(html_file_path, 'w', encoding='utf-8') as f:
        f.write(html)

    # Сохранение скриншота
    screenshot_file_path = base_dir / f"{company_name}.png"
    screenshot = Image.open(screenshot_data)  # Assuming screenshot_data is a file-like object
    screenshot.save(screenshot_file_path, format='PNG')

    # Сохранение JSON с информацией
    data = {
        'cms': cms,
        'language': language,
        'framework': framework,
        'external_js': external_js,
        'social_links': social_links
    }

    json_file_path = base_dir / f"{company_name}.json"
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)

    print(f"Данные по компании {company_name} успешно сохранены.")