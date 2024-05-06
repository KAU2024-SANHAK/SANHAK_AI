import pymysql.cursors

from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware
import uvicorn


app = FastAPI()

origins = [
    "http://localhost:5173",
    'https://honeyary.vercel.app',
    "http://localhost:8080",
    "http://0.0.0.0:8080",
    "http://127.0.0.1:8080",
    "https://www.honeyary-ai.o-r.kr",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT","PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

mysql_params = {
    'host': 'kkoolbee-database.cvimcwwiengv.ap-northeast-2.rds.amazonaws.com',
    'port': 3306,
    'user': 'admin',
    'password': 'sanhakkau11223344!!',
    'database': 'kkooldanji',
    'charset': 'utf8',
    'cursorclass': pymysql.cursors.DictCursor
}


@app.get('/api/ai/diary/summary')
async def get_diary_summary(request: Request):
    conn = pymysql.connect(**mysql_params)
    authorization_header = request.headers.get('Authorization')
    token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpYXQiOjE3MTQ4MTc2MDMsImV4cCI6MTc0NjM1MzYwMywibWVtYmVySWQiOjExfQ.dD7L0Lvbhszvgl8ACup067cJjlLKObMCQkUufrxgoez8l_B1YDlo0FhbUpL7ktu7Six2TtDNQetIZc8fzy9R8g"
    if authorization_header and authorization_header.startswith('Bearer'):
        token = authorization_header.split(' ')[1]

    date = request.query_params.get("date")

    try:
        with conn.cursor() as cursor:
            ## 주어진 date에 해당하는 년도와 해당 월에 작성된 일기의 감정을 분석
            query = "SELECT feeling FROM diary WHERE member_id = %s AND YEAR(writed_at) = %s AND MONTH(writed_at) = %s"
            cursor.execute(query, (token, date[:4] if date else None, date[5:7] if date else None))
            result = cursor.fetchall()
            feelings = [row['feeling'] for row in result]
        feeling_count = {
            "HAPPY": 0,
            "SAD": 0,
            "ANGRY": 0,
            "WORRY": 0,
            "SURPRISED": 0,
            "RELAXED": 0,
            "None": 0
        }

        # feeling_count = defaultdict(int)
        # for feeling in feelings:
        #     feeling_count[feeling] += 1
        #
        # max_feeling = max(feeling_count, key=feeling_count.get)
        # #두번째로 많은 감정도 선택
        # feeling_count[max_feeling] = 0
        # second_max_feeling = max(feeling_count, key=feeling_count.get)
    finally:
        conn.close()

    return {
        "status": 200,
        "message": "요청이 성공했습니다.",
        "data": {
            "firstFeeling": 0,
            "secondFeeling": 0
        }
    }


@app.get('/health', status_code=200)
async def get_health_check():
    return {
        "message": "요청이 성공했습니다.",
    }

if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=8080)
    
