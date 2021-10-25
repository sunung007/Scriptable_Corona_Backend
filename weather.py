import os
import math
import requests
import pytz
from datetime import datetime, timedelta
import json


status = {
    "sky": ["맑음", "구름조금", "구름많음", "흐림"],
    "rain": ["없음", "비", "비/눈", "눈", "소나기", "빗방울", "비/눈", "눈날림"],
    "icon": [
        # 공통
        "cloud.fill",  # 0. 흐림
        "cloud.heavyrain.fill",  # 1. 많은 비(비, 소나기)
        "cloud.sleet.fill",  # 2. 비/눈(빗방울/눈날림)
        "snow",  # 3. 눈(눈날림)
        # 아침
        "sun.max.fill",  # 4. 맑음
        "cloud.sun.fill",  # 5. 구름 조금
        "cloud.sun.fill",  # 6. 구름 많음
        "cloud.drizzle.fill",  # 7. 적은 비(비, 빗방울) + 일반
        "cloud.sun.rain.fill",  # 8. 비 + 구름 적음
        # 저녁
        "moon.stars.fill",  # 9. 맑음
        "cloud.moon.fill",  # 10. 구름 조금
        "cloud.moon.fill",  # 11. 구름 많음
        "cloud.drizzle.fill",  # 12. 적은 비(비, 빗방울)
        "cloud.moon.rain.fill",  # 13. 비 + 구름 적음
    ],
}


def get_grid(v1: float, v2: float) -> list:
    """Google 좌표계를 기상청 좌표계로 변환

    Args:
        v1 (float): 위도 (latitude)
        v2 (float): 경도 (longitude)

    Returns:
        list: int type list -> [grid_x, grid_y]
    """
    re = 6371.00877 / 5.0
    DEGRAD = math.pi / 180.0
    slat1 = 30.0 * DEGRAD
    slat2 = 60.0 * DEGRAD

    sn = math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(math.pi * 0.25 + slat1 * 0.5)
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
    sf = math.tan(math.pi * 0.25 + slat1 * 0.5)
    sf = math.pow(sf, sn) * math.cos(slat1) / sn
    ro = math.tan(math.pi * 0.25 + 19.0 * DEGRAD)
    ro = re * sf / math.pow(ro, sn)

    ra = math.tan(math.pi * 0.25 + (v1) * DEGRAD * 0.5)
    ra = re * sf / math.pow(ra, sn)

    theta = (v2 - 126.0) * DEGRAD
    if theta > math.pi:
        theta -= 2.0 * math.pi
    if theta < -math.pi:
        theta += 2.0 * math.pi
    theta *= sn

    return [
        math.floor(ra * math.sin(theta) + 43.5),
        math.floor(ro - ra * math.cos(theta) + 136.5),
    ]


def get_weather_info(all: list, category: str) -> str:
    """카테고리에 해당하는 날씨 파싱

    Args:
        all (list): 전체 날씨 정보
        category (str): 알고자 하는 날씨 정보(str code)

    Returns:
        str: 날씨 정보
    """
    # 카테고리 선택
    temp = list(filter(lambda i: i["category"] == category, all))
    # 가장 최근 일자의 예보 선택
    temp.sort(key=lambda l: (l["fcstDate"], l["fcstTime"]))
    return temp[0]["fcstValue"]


def get_weather_icon(rain: int, sky: int, volume: int) -> int:
    """날씨 정보에 해당하는 아이콘 index 계산

    Args:
        rain (int): 강우 상태
        sky (int): 하늘 상태
        volume (int): 강우량

    Returns:
        int: 아이콘 index
    """
    icon = 0
    if rain == 0:  # 맑음, 구름조금, 구름많음, 흐림(공통)
        icon = 0 if sky == 3 else sky + 4
    else:
        if rain == 3 or rain == 7:
            icon = 3  # 눈(공통)
        elif rain == 2 or rain == 6:
            icon = 2  # 비 + 눈(공통)
        else:  # 비
            if sky < 2:
                icon = 8  # 비 + 구름적음
            elif volume > 5:
                icon = 1  # 많은 비
            else:
                icon = 7  # 적은 비
    return icon


def get_weather_volume(info: str) -> int:
    """한글 강우량 -> 아이콘을 위한 index

    Args:
        info (str): 강우량 상태(한글 문자열)

    Returns:
        int: 강우량에 해당하는 index
    """
    info = info.strip()
    volume = 0
    try:
        if info == "1mm 미만":
            volume = 0  # 맑음
        elif info == "50mm 이상":
            volume = 10  # 많은 비
        else:
            volume = 5
    except:
        volume = 0
    return volume


def get_weather_icon_size(icon: str) -> list:
    """아이콘 별 적절한 크기

    Args:
        icon (str): Apple SF symbol 문자열

    Returns:
        list: 아이콘 별 적절한 크기 (width, height) -> int type list
    """
    width = 200
    height = 200
    if icon == "cloud.heavyrain.fill":
        height = 180
    elif icon == "cloud.fill" or icon == "cloud.sun.fill" or icon == "cloud.moon.fill":
        height = 150
    return [width, height]


def get_weather(nx: int, ny: int) -> dict:
    """날씨 정보 크롤링 및 정돈

    Args:
        nx (int): 기상청 X 좌표
        ny (int): 기상청 Y 좌표

    Returns:
        dict: 날씨 정보 및 아이콘 정보
    """
    global status

    # APP KEY
    APP_KEY = os.environ.get("DataGoKr_APP_KEY")
    # API URL
    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst"

    # 기준 시간 파싱
    KST = pytz.timezone("Asia/Seoul")
    now = datetime.now(KST)
    if int(str(now).split(":")[1]) < 45:
        now = now - timedelta(hours=1)

    base_hour = str(now.time()).split(":")[0]
    base_time = base_hour + "30"
    base_date = "".join(str(now.date()).split("-"))

    # API Request
    response = requests.get(
        url,
        params={
            "serviceKey": APP_KEY,
            "numOfRows": 60,
            "dataType": "JSON",
            "base_date": base_date,
            "base_time": base_time,
            "nx": nx,
            "ny": ny,
        },
    )
    if response.status_code != 200:
        return {"error": "날씨 정보 얻기에 실패하였습니다."}

    # 받아온 데이터
    data = response.json()["response"]
    if data["header"]["resultCode"] != "00":
        return {"error": "날씨 정보 얻기에 실패하였습니다."}

    data_body = data["body"]["items"]["item"]

    # 하늘 상태 구하기
    sky = int(get_weather_info(data_body, "SKY")) - 1
    rain = int(get_weather_info(data_body, "PTY"))
    sky_status = status["sky"][sky] if rain == 0 else status["rain"][rain]

    # 하늘 상태에 따른 아이콘 구하기
    volume_str = get_weather_info(data_body, "RN1")
    volume = get_weather_volume(volume_str)
    icon_index = get_weather_icon(rain, sky, volume)
    icon = status["icon"][icon_index]

    # 아이콘 크기 구하기
    icon_size = get_weather_icon_size(icon)

    return {
        "code": 200,  # 결과 정상 코드
        "temperature": get_weather_info(data_body, "T1H") + "℃",  # 온도
        "sky": sky_status,  # 하늘 상태
        "volume": volume,  # 강우량
        "icon": {  # 아이콘
            "icon": icon,
            "size": icon_size,
        },
    }
