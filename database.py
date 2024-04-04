import json
import pymysql.cursors
import datetime
from flask import Flask, request, jsonify


app = Flask(__name__)

mysql_params = {
    'host': '',
    'port': 3306,
    'user': '',
    'password': '',
    'database': '',
    'charset': 'utf8',
    'cursorclass': pymysql.cursors.DictCursor
}

conn = pymysql.connect(**mysql_params)


def current_user(request):
    ## 여기에 현재 로그인된 사용자 id를 반환하는 코드 작성
    ## api로 받아올 것
    return 1

def get_writeAt():
    ## 여기에 api가 요청된 시각을 반환하는 코드 작성
    return datetime.datetime.now().strftime('%Y-%m-%d')

@app.route('/diary', methods=['GET'])
def get_info():
    current_time = datetime.datetime.now().isoformat()
    user_id = current_user(request)
    return jsonify({
        'user_id': user_id,
        'current_time': current_time
    })

def to_dict(data):
    info_dict = json.loads(data)
    return info_dict

def get_keywords_from_db():
    try:
        with conn.cursor() as cursor:
            info_dict = to_dict(get_info())
            query = "SELECT * FROM diary WHERE member_id = %s AND date = %s"
            cursor.execute(query, (info_dict['user_id'], info_dict['current_time']))
            result = cursor.fetchall()
        return result
    finally:
        conn.close()


def insert_diary_to_db(where, values):
    try:
        with conn.cursor() as cursor:
            info_dict = to_dict(get_info())
            query = "UPDATE diary SET %s = %s WHERE member_id = %s AND date = %s"
            cursor.execute(query, (where, values, info_dict['user_id'], info_dict['current_time']))
        conn.commit()
    except Exception as e:
        print(e)



if __name__ == '__main__':
    app.run()