import os
import requests
import json, xmltodict


def get_covid_region(city: str) -> int:
    """시/도 이름 -> 코로나 라이브의 위치 인덱스

    Args:
        city (str): 시/도 이름

    Returns:
        int: 코로나 라이브에서 사용하는 위치 index
    """
    cities = {
        "서울특별시": 0,
        "부산광역시": 1,
        "대구광역시": 3,
        "인천광역시": 2,
        "광주광역시": 4,
        "대전광역시": 5,
        "울산광역시": 6,
        "세종특별자치시": 7,
        "경기도": 8,
        "강원도": 9,
        "충청북도": 10,
        "충청남도": 11,
        "전라북도": 14,
        "전라남도": 15,
        "경상북도": 12,
        "경상남도": 13,
        "제주특별자치도": 16,
        "이어도": 16,
    }
    return cities[city]


def get_covid_info(city: int) -> dict:
    """코로나 확진자 수

    Args:
        city (int): 코로나 라이브에서 사용하는 지역 index

    Returns:
        dict: 코로나 확진자 정보
    """
    url = "https://apiv3.corona-live.com/domestic/live.json"
    response = requests.get(url).json()
    result = {
        # [도시별 오늘 확진자 수, 어제 대비 증가 인원]
        "city": response["cities"][str(city)],
        # [전국 실시간 확진자 수, 어제 대비 증가 인원]
        "today": [
            response["live"]["today"],
            response["live"]["today"] - response["live"]["yesterday"],
        ],
        # [전체 확진자 수, 0시 기준 확진자 수]
        "total": [0, 0],
        "yesterday": 0,
    }

    # 이틀 전
    url = "https://apiv3.corona-live.com/domestic/stat.json"
    response = requests.get(url).json()
    result["total"] = response["overview"]["confirmed"]
    # result["yesterday"] = get_covid_day()  # 이틀 전 전국 확진자
    return result
