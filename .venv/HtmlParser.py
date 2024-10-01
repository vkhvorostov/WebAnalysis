import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path

def get_html_and_resources(url, save_dir):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error fetching page: {response.status_code}")
            return None

        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        save_resources(soup, url, save_dir)
        return html

    except Exception as e:
        print(f"Failed to fetch page: {e}")
        return None

def save_resources(soup, base_url, save_dir):
    resources_dir = Path(save_dir)
    os.makedirs(resources_dir, exist_ok=True)

    # Скачиваем и сохраняем JS, CSS и изображения
    for tag, attr, folder in [('script', 'src', 'js'), ('link', 'href', 'css'), ('img', 'src', 'images')]:
        elements = soup.find_all(tag)
        for element in elements:
            resource_url = element.get(attr)
            if resource_url:
                download_resource(resource_url, base_url, resources_dir / folder)

def download_resource(resource_url, base_url, save_dir):
    try:
        full_url = urljoin(base_url, resource_url)
        resource_name = os.path.basename(urlparse(full_url).path)
        if not resource_name:
            return

        os.makedirs(save_dir, exist_ok=True)
        resource_path = save_dir / resource_name

        response = requests.get(full_url)
        if response.status_code == 200:
            with open(resource_path, 'wb') as f:
                f.write(response.content)
            print(f"Resource saved: {resource_path}")
        else:
            print(f"Failed to download {full_url}")

    except Exception as e:
        print(f"Error downloading resource {resource_url}: {e}")