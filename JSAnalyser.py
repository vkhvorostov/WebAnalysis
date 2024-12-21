from bs4 import BeautifulSoup


def find_external_js(html):
    soup = BeautifulSoup(html, 'html.parser')
    scripts = soup.find_all('script', src=True)
    external_js = [script['src'] for script in scripts if script['src'].startswith('http')]
    return external_js


def find_social_links(html):
    soup = BeautifulSoup(html, 'html.parser')
    social_links = set()
    social_urls = ('facebook.com', 'vk.com', 'instagram.com', 'youtube.com', 'wa.me', 
                   't.me', 'whatsapp.com', 'whatsapp://')
    for a in soup.find_all('a', href=True):
        if any(domain in a['href'] for domain in social_urls):
            social_links.add(a['href'])
    return list(social_links)
