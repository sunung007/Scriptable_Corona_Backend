import os
import requests
import csv


def get_region_grid(nx:int, ny:int) -> list:
    """기상청 좌표계 -> 지역명

    Args:
        nx (float): x 좌표
        ny (float): y 좌표

    Returns:
        list: [시/도, 시/군/구, 읍/면/동]
    """
    loc_arr = []
    grid = list(map(str, [nx, ny]))

    with open('cities.csv', 'r', encoding='utf-8') as raw_file:
        for line in csv.reader(raw_file):
            if line[:2] == grid:
                loc_arr = line[2:]
                break

    return loc_arr


def get_region_coord(lat: float, lon: float, nx: int, ny: int) -> list:
    """좌표계 -> 지역명

    Args:
        lat (float): 위도 (latitude)
        lon (float): 경도 (longitude)
        nx (int): 기상청 X 좌표
        ny (int): 기상청 Y 좌표

    Returns:
        list: 지역명 list (시/도, 시/군/구, 읍/면/동, 기타)
    """
    CLIENT_ID = os.environ.get('SCRIPTABLE_CORONA_NAVER_ID')
    CLIENT_SECRET = os.environ.get('SCRIPTABLE_CORONA_NAVER_APP_KEY')

    url = 'https://naveropenapi.apigw.ntruss.com/map-reversegeocode/v2/gc?coords='\
        + str(lon) + "," + str(lat) \
            + "&output=json&orders=legalcode"

    response = requests.get(url, headers={
        'X-NCP-APIGW-API-KEY-ID': CLIENT_ID,
        'X-NCP-APIGW-API-KEY': CLIENT_SECRET
    })
    if response.status_code != 200:
        return get_region_grid(nx, ny)

    data = response.json()
    if data['status']['code'] != 0:
        return get_region_grid(nx, ny)
    data = data['results'][0]['region']

    result = []
    for area in data:
        if area == 'area0': continue
        if data[area]['name'] != "":
            result.append(data[area]['name'])
    
    return result