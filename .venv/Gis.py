import requests

# Функция для запроса организаций по API 2ГИС
def get_companies(city, industry):
    api_key = '94b6ea43-250c-4575-8523-ab7e59a4c8ad'
    url = f"https://catalog.api.2gis.ru/3.0/items"
    params = {
        'q': industry,
        'region_id': city,
        'fields': 'items.point,items.org,items.contact_groups',
        'key': api_key,
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()['result']['items']
    else:
        print(f"Error fetching data: {response.status_code}")
        return []
