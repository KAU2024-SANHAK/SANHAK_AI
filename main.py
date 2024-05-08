import asyncio
import traceback
import pymysql.cursors
import datetime
from diaryclass import diary
from collections import defaultdict
from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware
import uvicorn



app = FastAPI()

origins = [
    "./diaryclass.py",
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

async def connect_mysql():
    conn = await asyncio.wait_for(pymysql.connect(**mysql_params), timeout=None)
    return conn

@app.post('/api/ai/diary/create')
async def get_api_diary_create(request: Request):
    conn = await connect_mysql()
    data = await request.json()
    token = request.headers.get('Authorization')

    if token is None:
        return {
            "status": 401,
            "message": "토큰이 없습니다."
        }

    new_diary = diary(
        diary_content = diary.diary_content(
            feeling = data['feeling'],
            when = data['when'],
            where = data['where'],
            who = data['who'],
            what = data['what'],
            realized = data['realized']
        ),
        metadata=None,
        content=None,
        title=None,
        spicy_advice=None,
        soft_advice=None
    )

    new_diary.get_diary_completion()
    try:
        with conn.cursor() as cursor:
            query = "INSERT INTO diary (`title`, `content`, `member_id`) VALUES (%s, %s, %s)"
            cursor.execute(query, (new_diary.get_diary_data("title"), new_diary.get_diary_data("content"), token))
            diary_id = cursor.lastrowid
        conn.commit()
        with conn.cursor() as cursor:
            query = "UPDATE diary SET writed_at = %s WHERE member_id = %s AND diary_id = %s"
            cursor.execute(query, (datetime.datetime.now(), token, diary_id))

        if new_diary.get_diary_data("feeling") is None:
            get_diary_feelings()
            with conn.cursor() as cursor:
                query = "UPDATE diary SET feeling = %s WHERE member_id = %s AND diary_id = %s"
                cursor.execute(query, (new_diary.get_diary_data("feeling"), token, diary_id))
            conn.commit()
            # diary_id와 diaryContent가 null 값인지 확인하여 처리합니다.
        diary_id = diary_id if diary_id is not None else 0
        diary_content = new_diary.get_diary_data("content") if new_diary.get_diary_data("content") else ""

    except Exception as e:
        error_message = str(e)
        traceback_message = traceback.format_exc()
        return {
            "status": 500,
            "message": "요청이 실패했습니다.",
            "error": error_message,
            "traceback": traceback_message
        }

    finally:
        conn.close()

    return {
            "status": 201,
            "message": "요청이 성공했습니다.",
            "data": {
                "diaryId": diary_id,
                "diaryContent" : diary_content
            }
    }


@app.post('/api/ai/diary/feelings')
async def get_diary_feelings(request: Request):
    conn = await connect_mysql()
    data = await request.json()
    token = request.headers.get('Authorization')
    dairy_id = data['diaryId']

    if token is None:
        return {
            "status": 401,
            "message": "토큰이 없습니다."
        }

    if dairy_id is None:
        return {
            "status": 400,
            "message": "일기 ID가 없습니다."
        }

    try:
        with conn.cursor() as cursor:
            query = "SELECT content FROM diary WHERE member_id = %s AND diary_id = %s"
            cursor.execute(query, (token, dairy_id))
            diary_content = cursor.fetchone()

            diary_content = diary_content['content']

        new_diary = diary(
            diary_content = None,
            metadata=None,
            content=diary_content,
            title=None,
            spicy_advice=None,
            soft_advice=None
        )

        new_diary.get_diary_feeling()
        # feeling이 null인 경우를 처리합니다.
        feeling = new_diary.get_diary_data("feeling") if new_diary.get_diary_data("feeling") else ""

        with conn.cursor() as cursor:
            query = "UPDATE diary SET feeling = %s WHERE member_id = %s AND diary_id = %s"
            cursor.execute(query, (feeling, token, dairy_id))
        conn.commit()

    except Exception as e:
        error_message = str(e)
        traceback_message = traceback.format_exc()
        return {
            "status": 500,
            "message": "요청이 실패했습니다.",
            "error": error_message,
            "traceback": traceback_message
        }
    finally:
        conn.close()


    return {
        "status": 201,
        "message": "요청이 성공했습니다.",
        "data": {
            "feeling": feeling
        }
    }


@app.post('/api/ai/advice/content')
async def get_diary_advice(request: Request):
    conn = await connect_mysql()
    data = await request.json()
    token = request.headers.get('Authorization')
    dairy_id = data['diaryId']

    if token is None:
        return {
            "status": 401,
            "message": "토큰이 없습니다."
        }

    if dairy_id is None:
        return {
            "status": 400,
            "message": "일기 ID가 없습니다."
        }

    try:
        with conn.cursor() as cursor:
            query = "SELECT content FROM diary WHERE member_id = %s AND diary_id = %s"
            cursor.execute(query, (token, dairy_id))
        diary_content = cursor.fetchone()

        new_diary = diary(
            diary_content = None,
            metadata=None,
            content=diary_content,
            title=None,
            spicy_advice=None,
            soft_advice=None
        )

        new_diary.get_diary_advice()

        with conn.cursor() as cursor:
            query = "INSERT INTO advice (kind_advice, spicy_advice) VALUES (%s, %s)"
            cursor.execute(query, (new_diary.get_diary_data("soft_advice"), new_diary.get_diary_data("spicy_advice")))
            adviceid = cursor.lastrowid
            query = "UPDATE diary SET advice_id = %s WHERE member_id = %s AND diary_id = %s"
            cursor.execute(query, (adviceid, token, dairy_id))
        conn.commit()
         # adviceId, spicy, kind가 null인 경우를 처리합니다.
        advice_id = adviceid if adviceid is not None else 0
        spicy_advice = new_diary.get_diary_data("spicy_advice") if new_diary.get_diary_data("spicy_advice") else ""
        soft_advice = new_diary.get_diary_data("soft_advice") if new_diary.get_diary_data("soft_advice") else ""

    except Exception as e:
        error_message = str(e)
        traceback_message = traceback.format_exc()
        return {
            "status": 500,
            "message": "요청이 실패했습니다.",
            "error": error_message,
            "traceback": traceback_message
        }

    finally:
        conn.close()

   
    return {
        "status": 201,
        "message": "요청이 성공했습니다.",
        "data": {
           "adviceId": advice_id,
            "advice": {
                "spicy": spicy_advice,
                "kind": soft_advice
            }
        }
    }


@app.get('/api/ai/diary/summary')
async def get_diary_summary(request: Request):
    conn = await connect_mysql()
    token = request.headers.get('Authorization')
    date = request.query_params.get("date")

    if token is None:
        return {
            "status": 401,
            "message": "토큰이 없습니다."
        }

    if date is None:
        return {
            "status": 400,
            "message": "날짜가 없습니다."
        }

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
        if not feelings:  # 쿼리 결과가 비어 있는 경우
            # 쿼리 결과가 비어 있는 경우, 기본값으로 처리합니다.
            max_feeling = "None"
            second_max_feeling = "None"
        else:
            feeling_count = defaultdict(int)
        for feeling in feelings:
            feeling_count[feeling] += 1

        max_feeling = max(feeling_count, key=feeling_count.get)
        #두번째로 많은 감정도 선택
        feeling_count[max_feeling] = 0
        second_max_feeling = max(feeling_count, key=feeling_count.get)


    except Exception as e:
        error_message = str(e)
        traceback_message = traceback.format_exc()
        return {
            "status": 500,
            "message": "요청이 실패했습니다.",
            "error": error_message,
            "traceback": traceback_message
        }

    finally:
        conn.close()

    return {
        "status": 200,
        "message": "요청이 성공했습니다.",
        "data": {
            "firstFeeling": max_feeling,
            "secondFeeling": second_max_feeling
        }
    }



if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=8080)
    
