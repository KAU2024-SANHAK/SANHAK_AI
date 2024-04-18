import json
import pymysql.cursors
import datetime
from flask import Flask, request, jsonify
from diaryclass import diary


app = Flask(__name__)

mysql_params = {
    'host': 'kkoolbee-database.cvimcwwiengv.ap-northeast-2.rds.amazonaws.com',
    'port': 3306,
    'user': 'admin',
    'password': 'sanhakkau11223344!!',
    'database': 'kkooldanji',
    'charset': 'utf8',
    'cursorclass': pymysql.cursors.DictCursor
}

conn = pymysql.connect(**mysql_params)


@app.route('/diary', methods=['GET'])
def get_api_diary_create():
    data = request.json
    token = request.headers.get('Authorization')

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
        conn.commit()
        with conn.cursor() as cursor:
            query = "SELECT diary_id FROM diary WHERE member_id = %s AND title = %s"
            cursor.execute(query, (token, new_diary.get_diary_data("title")))
            result = cursor.fetchone()

    finally:
        conn.close()

    diary_id = result

    return jsonify({
        "status": 201,
        "message": "요청이 성공했습니다.",
        "data": {
            "diaryId": diary_id,
            "diaryContent" : new_diary.get_diary_data("content")
        }
    }), 201


@app.route('/api/ai/diary/feelings', methods=['POST'])
def get_diary_feelings():
    data = request.json
    token = request.headers.get('Authorization')
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
            "feeling1": new_diary.get_diary_data("feeling")
        }
    }), 201


@app.route('/api/ai/advice/content', methods=['POST'])
def get_diary_advice():
    data = request.json
    token = request.headers.get('Authorization')
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
            query = "INSERT INTO advice (kind_advice, spicy_advice)"
            cursor.execute(query, (new_diary.get_diary_data("soft_advice"), new_diary.get_diary_data("spicy_advice")))
        conn.commit()
        with conn.cursor() as cursor:
            query = "SELECT id FROM advice WHERE kind_advice = %s AND spicy_advice = %s"
            cursor.execute(query, (new_diary.get_diary_data("soft_advice"), new_diary.get_diary_data("spicy_advice")))
            adviceId = cursor.fetchone()
            query = "UPDATE diary SET advice_id = %s WHERE member_id = %s AND diary_id = %s"
            cursor.execute(query, (adviceId, token, dairy_id))
        conn.commit()
    finally:
        conn.close()

    return jsonify({
        "status": 201,
        "message": "요청이 성공했습니다.",
        "data": {
            "adviceId": adviceId,
            "advice": {
                "spicy": new_diary.get_diary_data("spicy_advice"),
                "kind": new_diary.get_diary_data("soft_advice")
            }
        }
    }), 201


@app.route('/api/ai/diary/summary', methods=['GET'])
def get_diary_summary():
    token = request.headers.get('Authorization')

    try:
        with conn.cursor() as cursor:
            query = "SELECT feeling FROM diary WHERE member_id = %s AND "
            cursor.execute(query, token)
            result = cursor.fetchall()
        return result
    finally:
        conn.close()




if __name__ == '__main__':
    app.run()