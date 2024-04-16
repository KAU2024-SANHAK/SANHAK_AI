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
    insert_diary_to_db("content", new_diary.get_diary_data("content"), token)
    insert_diary_to_db("title", new_diary.get_diary_data("title"), token)

    def find_diary_id():
        try:
            with conn.cursor() as cursor:
                query = "SELECT diary_id FROM diary WHERE member_id = %s AND title = %s"
                cursor.execute(query, )
                result = cursor.fetchone()
            return result
        finally:
            conn.close()
            return 0

    diary_id = find_diary_id()


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

    diary_content = get_data_from_db("content", token, dairy_id)

    new_diary = diary(
        diary_content = None,
        metadata=None,
        content=diary_content,
        title=None,
        spicy_advice=None,
        soft_advice=None
    )

    def insert_feeling_to_db(feeling):
        try:
            with conn.cursor() as cursor:
                query = "UPDATE diary SET feeling = %s WHERE member_id = %s AND diary_id = %s"
                cursor.execute(query, (feeling, token, dairy_id))
            conn.commit()
        finally:
            conn.close()
            return 0

    new_diary.get_diary_feeling()
    insert_feeling_to_db(new_diary.get_diary_data("feeling"))


    return jsonify({
        "status": 201,
        "message": "요청이 성공했습니다.",
        "data": {
            "feeling1": new_diary.get_diary_data("feeling")[0],
            "feeling2": new_diary.get_diary_data("feeling")[1]
        }
    }), 201


@app.route('/api/ai/advice/content', methods=['POST'])
def get_diary_davice():
    data = request.json
    token = request.headers.get('Authorization')
    dairy_id = data['diaryId']

    diary_content = get_data_from_db("content", token, dairy_id)

    new_diary = diary(
        diary_content = None,
        metadata=None,
        content=diary_content,
        title=None,
        spicy_advice=None,
        soft_advice=None
    )

    new_diary.get_diary_advice()

    def insert_advice_to_db(kind, spicy):
        try:
            with conn.cursor() as cursor:
                query = "INSERT INTO advice (kind_advice, spicy_advice)"
                cursor.execute(query, (kind, spicy))
            conn.commit()
        finally:
            conn.close()
            return 0

    insert_advice_to_db(new_diary.get_diary_data("soft_advice"), new_diary.get_diary_data("spicy_advice"))

    try:
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



def get_data_from_db(what, member_id, diary_id):
    try:
        with conn.cursor() as cursor:
            query = "SELECT %s FROM diary WHERE member_id = %s AND diary_id = %s"
            cursor.execute(query, (what, member_id, diary_id))
            result = cursor.fetchall()
        return result
    finally:
        conn.close()


def insert_diary_to_db(where, values, member_id):
    try:
        with conn.cursor() as cursor:
            query = "UPDATE diary SET %s = %s WHERE member_id = %s"
            cursor.execute(query, (where, values, member_id))
        conn.commit()
    except Exception as e:
        print(e)



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