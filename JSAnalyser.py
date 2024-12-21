from bs4 import BeautifulSoup

def find_external_js(html):
    soup = BeautifulSoup(html, 'html.parser')
    scripts = soup.find_all('script', src=True)
    external_js = [script['src'] for script in scripts if script['src'].startswith('http')]
    return external_js

def find_social_links(html):
    soup = BeautifulSoup(html, 'html.parser')
    social_links = []
    for a in soup.find_all('a', href=True):
        if any(domain in a['href'] for domain in ['facebook.com', 'vk.com', 'instagram.com']):
            social_links.append(a['href'])
    return social_links