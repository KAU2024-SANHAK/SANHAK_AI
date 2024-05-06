import json
import pymysql.cursors
import datetime
from flask import Flask, request, jsonify
from diaryclass import diary
from collections import defaultdict
from fastapi import FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware
import uvicorn


app = FastAPI()

# origins = [
#     "http://localhost:5173",
#     'https://honeyary.vercel.app',
#     "http://localhost:8080",
#     "http://0.0.0.0:8080",
#     "http://127.0.0.1:8080",
#     "https://www.honeyary-ai.o-r.kr",
# ]
app.add_middleware(
    CORSMiddleware,
    allow_origins= [
    "http://localhost:5173",
    'https://honeyary.vercel.app',
    "http://localhost:8080",
    "http://0.0.0.0:8080",
    "http://127.0.0.1:8080",
    "https://www.honeyary-ai.o-r.kr",
],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT","PATCH", "DELETE"],
    allow_headers=["*"],
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


@app.post('/api/ai/diary/create')
async def get_api_diary_create():
    conn = pymysql.connect(**mysql_params)
    data = request.json
    authorization_header = request.headers.get('Authorization')
    if authorization_header and authorization_header.startswith('Bearer'): token = authorization_header.split(' ')[1]

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
    finally:
        conn.close()


    return jsonify({
        "status": 201,
        "message": "요청이 성공했습니다.",
        "data": {
            "diaryId": diary_id,
            "diaryContent" : new_diary.get_diary_data("content")
        }
    }), 201


@app.post('/api/ai/diary/feelings')
async def get_diary_feelings():
    conn = pymysql.connect(**mysql_params)
    data = request.json
    authorization_header = request.headers.get('Authorization')
    if authorization_header and authorization_header.startswith('Bearer'): token = authorization_header.split(' ')[1]
    dairy_id = data['diaryId']

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
        with conn.cursor() as cursor:
            query = "UPDATE diary SET feeling = %s WHERE member_id = %s AND diary_id = %s"
            cursor.execute(query, (new_diary.get_diary_data("feeling"), token, dairy_id))
        conn.commit()
    finally:
        conn.close()


    return jsonify({
        "status": 201,
        "message": "요청이 성공했습니다.",
        "data": {
            "feeling": new_diary.get_diary_data("feeling")
        }
    }), 201


@app.post('/api/ai/advice/content')
async def get_diary_advice():
    conn = pymysql.connect(**mysql_params)
    data = request.json
    authorization_header = request.headers.get('Authorization')
    if authorization_header and authorization_header.startswith('Bearer'): token = authorization_header.split(' ')[1]
    dairy_id = data['diaryId']

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
    finally:
        conn.close()

    return jsonify({
        "status": 201,
        "message": "요청이 성공했습니다.",
        "data": {
            "adviceId": adviceid,
            "advice": {
                "spicy": new_diary.get_diary_data("spicy_advice"),
                "kind": new_diary.get_diary_data("soft_advice")
            }
        }
    }), 201


@app.get('/api/ai/diary/summary')
async def get_diary_summary():
    conn = pymysql.connect(**mysql_params)
    authorization_header = request.headers.get('Authorization')
    if authorization_header and authorization_header.startswith('Bearer'): token = authorization_header.split(' ')[1]
    date = request.args.get('date')

    try:
        with conn.cursor() as cursor:
            ## 주어진 date에 해당하는 년도와 해당 월에 작성된 일기의 감정을 분석
            query = "SELECT feeling FROM diary WHERE member_id = %s AND YEAR(writed_at) = %s AND MONTH(writed_at) = %s"
            cursor.execute(query, (token, date[:4], date[5:7]))
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

        feeling_count = defaultdict(int)
        for feeling in feelings:
            feeling_count[feeling] += 1

        max_feeling = max(feeling_count, key=feeling_count.get)
        #두번째로 많은 감정도 선택
        feeling_count[max_feeling] = 0
        second_max_feeling = max(feeling_count, key=feeling_count.get)
    finally:
        conn.close()

    return jsonify({
        "status": 200,
        "message": "요청이 성공했습니다.",
        "data": {
            "firstFeeling": max_feeling,
            "secondFeeling": second_max_feeling
        }
    }), 200


if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=8080)
    