import csv

def main():
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

    with open('cities.csv', 'r', encoding='utf-8') as raw_file:
        for line in csv.reader(raw_file):
            print(line)
            print(line[2:])

main()