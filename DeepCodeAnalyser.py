import re

def detect_cms(html):
    if 'wp-content' in html or 'wordpress' in html:
        return 'WordPress'
    elif 'bitrix' in html:
        return 'Bitrix'
    else:
        return 'Unknown'

def detect_language(headers):
    server = headers.get('Server', '').lower()
    if 'php' in server:
        return 'PHP'
    elif 'python' in server:
        return 'Python'
    else:
        return 'Unknown'

def detect_framework(headers):
    if 'X-Powered-By' in headers:
        if 'laravel' in headers['X-Powered-By'].lower():
            return 'Laravel'
        elif 'symfony' in headers['X-Powered-By'].lower():
            return 'Symfony'
    return 'Unknown'