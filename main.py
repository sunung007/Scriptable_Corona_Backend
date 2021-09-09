import os
import requests
import math
from flask import Flask, request as flaskRequest
from datetime import datetime, timedelta


app = Flask(__name__)
APP_KEY = os.environ.get('DataGoKr_APP_KEY')


def get_weather(v1, v2):
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

    [nx, ny] = get_grid(v1, v2)

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
    icon = get_weather_icon(rain, sky, volume)

    return {
        'code': 200,                                            # 결과 정상 코드
        'temperature': get_weather_info(data_body, 'T1H')+'℃',  # 온도
        'sky': sky_status,                                      # 하늘 상태
        'volume': volume,                                       # 강우량
        'icon': status['icon'][icon]                            # 아이콘
    }


def get_covid_info(city):
    url = 'https://apiv2.corona-live.com/domestic-init.json'
    response = requests.get(url).json()
    return {
        'city': response['citiesLive'][str(city)],      # [도시별 오늘 확진자 수, 어제 대비 증가 인원]
        'total': response['stats']['cases'],            # [전체 확진자 수, 0시 기준 확진자 수]
        'today': [response['statsLive']['today'],       # [전국 실시간 확진자 수, 어제 대비 증가 인원]
                  response['statsLive']['today']-response['statsLive']['yesterday']]
    }


@app.route('/api', methods=['GET'])
def api():
    params = flaskRequest.args.to_dict()
    if len(params) == 0:    # error handle
        return "Gofo API - Error : 잘못된 요청입니다. 파라미터를 확인해주세요."
    elif not('lang' in params and 'long' in params):
        return "Gofo API - Error : 잘못된 요청입니다. 파라미터를 확인해주세요."

    [lang, long] = list(map(float, [params['lang'], params['long']]))

    covid = get_covid_info(0)
    weather = get_weather(lang, long)
    return {
        'covid': covid,
        'weather': weather,
    } if weather != 'error' else ''


@app.route('/')
def root():
    return "Gofo API - Scriptable Corona Widget"


if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=8080)
    app.run()