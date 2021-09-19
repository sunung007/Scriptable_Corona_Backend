# Gofo(sunung007)
# Scriptbale Corona 위젯을 위한 BE
# BE URL : https://gofo-corona.herokuapp.com/

import os
import math
import csv
import requests
from datetime import datetime, timedelta
from flask import Flask, request as flaskRequest


app = Flask(__name__)
APP_KEY = os.environ.get('DataGoKr_APP_KEY')


def get_grid(v1, v2) :
    re = 6371.00877 / 5.0
    DEGRAD = math.pi / 180.0
    slat1 = 30.0  * DEGRAD
    slat2 = 60.0 * DEGRAD

    sn = math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(math.pi * 0.25 + slat1 * 0.5)
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
    sf = math.tan(math.pi * 0.25 + slat1 * 0.5)
    sf = math.pow(sf, sn) * math.cos(slat1) / sn
    ro = math.tan(math.pi * 0.25 + 19.0 * DEGRAD)
    ro = re * sf / math.pow(ro, sn);

    ra = math.tan(math.pi * 0.25 + (v1) * DEGRAD * 0.5)
    ra = re * sf / math.pow(ra, sn)

    theta = (v2 - 126.0) * DEGRAD
    if theta > math.pi :
        theta -= 2.0 * math.pi
    if theta < -math.pi :
        theta += 2.0 * math.pi
    theta *= sn

    return [math.floor(ra * math.sin(theta) + 43.5),
            math.floor(ro - ra * math.cos(theta) + 136.5)]


def get_weather(nx, ny):
    def get_weather_info(all, weather):
        return list(filter(lambda i : i['category']==weather, all))[0]['fcstValue']
    def get_weather_icon(rain, sky, volume):
        icon = 0
        if rain == 0:                           # 맑음, 구름조금, 구름많음, 흐림(공통)
            icon = 0 if sky==3 else sky+4
        else:   
            if rain==3 or rain==7: icon = 3     # 눈(공통)
            elif rain==2 or rain==6: icon = 2   # 비 + 눈(공통)
            else:                               # 비
                if sky < 2: icon = 8            # 비 + 구름적음
                elif volume > 5: icon = 1       # 많은 비
                else: icon = 7                  # 적은 비
        return icon
    def get_weather_icon_size(icon):
        width = 200
        height = 200
        if icon == 'cloud.heavyrain.fill':
            height = 180
        elif icon == 'cloud.fill' or icon == 'cloud.sun.fill' or icon == 'cloud.moon.fill':
            height = 150
        return [width, height]


    status = {
        'sky': ['맑음', '구름조금', '구름많음', '흐림'],
        'rain': ['없음', '비', '비/눈', '눈', '소나기', '빗방울', '비/눈', '눈날림'],
        'icon': [
                                    # 공통
            'cloud.fill',           # 0. 흐림
            'cloud.heavyrain.fill', # 1. 많은 비(비, 소나기)
            'cloud.sleet.fill',     # 2. 비/눈(빗방울/눈날림)
            'snow',                 # 3. 눈(눈날림)
                                    # 아침
            'sun.max.fill',         # 4. 맑음
            'cloud.sun.fill',       # 5. 구름 조금
            'cloud.sun.fill',       # 6. 구름 많음
            'cloud.drizzle.fill',   # 7. 적은 비(비, 빗방울) + 일반
            'cloud.sun.rain.fill',  # 8. 비 + 구름 적음
                                    # 저녁
            'moon.stars.fill',      # 9. 맑음
            'cloud.moon.fill',      # 10. 구름 조금
            'cloud.moon.fill',      # 11. 구름 많음
            'cloud.drizzle.fill',   # 12. 적은 비(비, 빗방울)
            'cloud.moon.rain.fill'  # 13. 비 + 구름 적음
        ]
    }

    now = datetime.now()
    if int(str(now).split(':')[1]) < 45:
        now = now - timedelta(hours=1)
    
    url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst'
    response = requests.get(url, params={
        'serviceKey': APP_KEY,
        'numOfRows': 60,
        'dataType': 'JSON',
        'base_date': ''.join(str(now.date()).split('-')),
        'base_time': str(now.time()).split(':')[0] + '30',
        'nx': nx,
        'ny': ny,
    })

    data = response.json()['response']
    data_code = data['header']['resultCode']
    if data_code != '00': # error handle
        return 'error'

    data_body = data['body']['items']['item']
    
    # 하늘 상태 구하기
    sky = int(get_weather_info(data_body, 'SKY'))-1
    rain = int(get_weather_info(data_body, 'PTY'))
    sky_status = status['sky'][sky] if rain==0 else status['rain'][rain]

    # 하늘 상태에 따른 아이콘 구하기
    volume = get_weather_info(data_body, 'RN1')
    icon_index = get_weather_icon(rain, sky, volume)
    icon = status['icon'][icon_index]

    # 아이콘 크기 구하기
    icon_size = get_weather_icon_size(icon)

    return {
        'code': 200,                                            # 결과 정상 코드
        'temperature': get_weather_info(data_body, 'T1H')+'℃',  # 온도
        'sky': sky_status,                                      # 하늘 상태
        'volume': volume,                                       # 강우량
        'icon': {
            'icon': icon,                       # 아이콘
            'size': icon_size,
        }
    }


def get_covid_info(city):
    # 어제 정보
    url = 'https://apiv2.corona-live.com/domestic-init.json'
    response = requests.get(url).json()
    result = {
        'city': response['citiesLive'][str(city)],      # [도시별 오늘 확진자 수, 어제 대비 증가 인원]
        'total': response['stats']['cases'],            # [전체 확진자 수, 0시 기준 확진자 수]
        'today': [response['statsLive']['today'],       # [전국 실시간 확진자 수, 어제 대비 증가 인원]
                  response['statsLive']['today']-response['statsLive']['yesterday']]
    }

    # 이틀 전
    url = 'https://apiv2.corona-live.com/cases-v2/week.json'
    response = requests.get(url).json()
    keys = [key for key in response]
    keys.sort()
    result['yesterday'] = sum(response[keys[-2]])       # 이틀 전 전국 확진자

    return result


def get_covid_region(city):
    cities = {
        '서울특별시': 0,
        '부산광역시': 1,
        '대구광역시': 3,
        '인천광역시': 2,
        '광주광역시': 4,
        '대전광역시': 5,
        '울산광역시': 6,
        '세종특별자치시': 7,
        '경기도': 8,
        '강원도': 9,
        '충청북도': 10,
        '충청남도': 11,
        '전라북도': 14,
        '전라남도': 15,
        '경상북도': 12,
        '경상남도': 13,
        '제주특별자치도': 16,
        '이어도': 16,
    }
    return cities[city]


def get_region(nx, ny):
    loc_arr = None
    grid = list(map(str, [nx, ny]))

    with open('cities.csv', 'r', encoding='utf-8') as raw_file:
        for line in csv.reader(raw_file):
            if line[:2] == grid:
                loc_arr = line[2:]
                break

    return loc_arr


@app.route('/api', methods=['GET'])
def api():
    params = flaskRequest.args.to_dict()
    if len(params) == 0:    # error handle
        return {'error': "Gofo API - Error : 잘못된 요청입니다. 파라미터를 확인해주세요."}
    elif not('lang' in params and 'long' in params or 'region' in params):
        return {'error': "Gofo API - Error : 잘못된 요청입니다. 파라미터를 확인해주세요."}

    [lang, long] = list(map(float, [params['lang'], params['long']]))
    [nx, ny] = get_grid(lang, long)

    if lang>43 or lang<33 or long>132 or long<124:
        return {'error': "Gofo API - Error : 잘못된 위치 정보입니다."}

    region = get_region(nx, ny)
    covid_region = int(params['region'])
    # covid_region = get_covid_region(region[0])
    covid = get_covid_info(covid_region)
    weather = get_weather(nx, ny)

    return {
        'region': region,
        'covid': covid,
        # 'covid_region': covid_region,
        'weather': weather,
    } if weather != 'error' else {'error': "Gofo API - Error : 데이터 로드에 실패하였습니다."}


@app.route('/')
def root():
    return "Gofo API - Scriptable Corona Widget"


if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=8080)
    app.run()