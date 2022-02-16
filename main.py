# Gofo(sunung007)
# Scriptbale Corona 위젯을 위한 BE
# BE URL : https://gofo-corona.herokuapp.com/

from flask import Flask, request as flaskRequest

from weather import *
from region import *
from covid import *

app = Flask(__name__)


@app.errorhandler(404)
def error():
    return {"error": "잘못된 링크입니다."}


@app.route("/")
def root():
    return "Gofo API - Scriptable Corona Widget"


@app.route("/api", methods=["GET"])
def api():
    # 파라미터
    params = flaskRequest.args.to_dict()
    if len(params) == 0 or not (
        "lang" in params and "long" in params and "region" in params
    ):
        return {"error": "잘못된 요청입니다. 파라미터를 확인해주세요."}

    # 파라미터 정보
    lat, lon = map(float, [params["lang"], params["long"]])
    covid_region = int(params["region"])

    # Google 좌표 -> 기상청 grid
    [nx, ny] = get_grid(lat, lon)
    # 기상청 grid -> 지역명
    region = get_region_coord(lat, lon, nx, ny)
    # 날씨 정보
    weather = get_weather(nx, ny)
    # 코로나 확진자 정보
    covid = get_covid_info(covid_region)

    if "error" in weather:
        return {
            "error": "데이터 로드에 실패하였습니다.",
        }
    else:
        return {
            "region": region,
            "covid": covid,
            "weather": weather,
        }


if __name__ == "__main__":
    # app.run(debug=True)
    app.run()
