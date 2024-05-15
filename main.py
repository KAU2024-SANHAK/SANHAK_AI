import aiomysql
import traceback
import datetime
import diaryclass as diary
from collections import defaultdict
from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware
import uvicorn
import tracemalloc
tracemalloc.start()




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
    'cursorclass': aiomysql.cursors.DictCursor
}

async def connect_mysql():
    try:
        conn = await aiomysql.connect(
            host=mysql_params['host'],
            port=mysql_params['port'],
            user=mysql_params['user'],
            password=mysql_params['password'],
            db=mysql_params['database'],
            charset=mysql_params['charset'],
            cursorclass=aiomysql.cursors.DictCursor
        )
        return conn
    except Exception as e:
        error_message = str(e)
        traceback_message = traceback.format_exc()
        print("MySQL connection failed:", error_message)
        return None

@app.post('/api/ai/diary/create')
async def get_api_diary_create(request: Request):
    conn = await connect_mysql()
    if conn is None:
        return {
            "status": 500,
            "message": "MySQL 연결에 실패했습니다."
        }
    data = await request.json()
    member_id = request.headers.get('Authorization')

    if member_id is None:
        return {
            "status": 401,
            "message": "헤더에 memberId가 없습니다."
        }

    new_diary = diary.DiaryCompletion(
        member_id=member_id,
        created_at=None,
        updated_at=None,
        written_at=None,
        when=data.get('when'),
        where=data.get('where'),
        who=data.get('who'),
        what=data.get('what'),
        realized=data.get('realized'),
        feeling=data.get('feeling')
    )

    await new_diary.get_diary_completion()
    new_diary.created_at = datetime.datetime.now()
    new_diary.updated_at = datetime.datetime.now()
    new_diary.written_at = datetime.datetime.now()

    if await new_diary.get_diary_data("feeling") is None:
        new_feeling = diary.DiaryFeeling(
            member_id=member_id,
            created_at=None,
            updated_at=None,
            written_at=None,
            content=await new_diary.get_diary_data("content")
        )
        await new_feeling.get_diary_feeling()

        feeling = new_feeling.feeling
        print("1번", feeling)
    else:
        feeling = new_diary.diary_data["feeling"]
        print("2번", feeling)


    try:
        async with conn.cursor() as cursor:
            title = new_diary.title
            content = new_diary.content
            writed_at = new_diary.written_at
            updated_at = new_diary.updated_at
            created_at = new_diary.created_at
            image = ("https://kkoolbee-storage.s3.ap-northeast-2.amazonaws.com/"
                     "dcb22ba3-b562-4c60-83ad-2814c7d07dca-"
                     "%E1%84%92%E1%85%A5%E1%84%82%E1%85%B5%E1%84%8B%E1%85%A5%E1%84%85%E1%85%B5%E1%84%89%E1%85%A5%E1%"
                     "84%87%E1%85%A5%E1%84%8C%E1%85%B5%E1%86%AB%E1%84%8D%E1%85%A1.png")
            query = ("INSERT INTO diary (`title`, `content`, `writed_at`,`created_at`,"
                     "`updated_at`, `feeling`, `member_id`, `imageurl`) "
                     "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)")
            await cursor.execute(query, (title, content, writed_at, created_at,
                                         updated_at, feeling, member_id, image))
            diary_id = cursor.lastrowid

            await conn.commit()

            # diary_id와 diaryContent가 null 값인지 확인하여 처리합니다.
        diary_id = diary_id if diary_id is not None else 0
        diary_content = await new_diary.get_diary_data("content") if await new_diary.get_diary_data("content") else ""

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
                "title": title,
                "diaryContent": diary_content,
                "feeling": feeling,
                "writed_at": writed_at,
                "imageurl": image
            }
    }


@app.post('/api/ai/diary/feeling')
async def get_diary_feelings(request: Request):
    conn = await connect_mysql()
    if conn is None:
        return {
            "status": 500,
            "message": "MySQL 연결에 실패했습니다."
        }
    data = await request.json()
    member_id = request.headers.get('Authorization')
    dairy_id = data.get('diaryId')

    print(member_id, dairy_id)
    if member_id is None:
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
        async with conn.cursor() as cursor:
            query = "SELECT content FROM diary WHERE member_id = %s AND diary_id = %s"
            await cursor.execute(query, (member_id, dairy_id))
            diary_content = await cursor.fetchone()

            diary_content = diary_content['content']
            print(diary_content)

        new_feeling = diary.DiaryFeeling(
            member_id=member_id,
            created_at=None,
            updated_at=None,
            written_at=None,
            content=diary_content
        )

        await new_feeling.get_diary_feeling()
        feelings = new_feeling.feeling
        if feelings is None:
            return {
                "status": 400,
                "message": "감정 분석에 실패했습니다."
            }
        print(feelings)

        async with conn.cursor() as cursor:
            query = "UPDATE diary SET feeling = %s WHERE member_id = %s AND diary_id = %s"
            await cursor.execute(query, (feelings, member_id, dairy_id))
        await conn.commit()

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
            "feeling": feelings
        }
    }


@app.post('/api/ai/advice/content')
async def get_diary_advice(request: Request):
    conn = await connect_mysql()
    if conn is None:
        return {
            "status": 500,
            "message": "MySQL 연결에 실패했습니다."
        }
    data = await request.json()
    member_id = request.headers.get('Authorization')
    dairy_id = data.get('diaryId')

    if member_id is None:
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
        async with conn.cursor() as cursor:
            query = "SELECT content FROM diary WHERE member_id = %s AND diary_id = %s"
            await cursor.execute(query, (member_id, dairy_id))
        diary_content = await cursor.fetchone()

        new_advice = diary.DiaryAdvice(
            member_id=member_id,
            created_at=None,
            updated_at=None,
            written_at=None,
            content=diary_content['content']
        )

        await new_advice.get_diary_advice()

        async with conn.cursor() as cursor:
            soft_advice = new_advice.soft_advice
            spicy_advice = new_advice.spicy_advice

            query = "INSERT INTO advice (kind_advice, spicy_advice) VALUES (%s, %s)"
            await cursor.execute(query, (soft_advice, spicy_advice))
            advice_id = cursor.lastrowid
            query = "UPDATE diary SET advice_id = %s WHERE member_id = %s AND diary_id = %s"
            await cursor.execute(query, (advice_id, member_id, dairy_id))
        await conn.commit()


         # adviceId, spicy, kind가 null인 경우를 처리합니다.
        advice_id = advice_id if advice_id is not None else 0
        spicy_advice = new_advice.spicy_advice if new_advice.spicy_advice else ""
        soft_advice = new_advice.soft_advice if new_advice.soft_advice else ""

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
    if conn is None:
        return {
            "status": 500,
            "message": "MySQL 연결에 실패했습니다."
        }
    member_id = request.headers.get('Authorization')
    date = datetime.datetime.now()

    if member_id is None:
        return {
            "status": 401,
            "message": "토큰이 없습니다."
        }

    try:
        async with conn.cursor() as cursor:
            ## 주어진 date에 해당하는 년도와 해당 월에 작성된 일기의 감정을 분석
            query = "SELECT feeling FROM diary WHERE member_id = %s AND YEAR(writed_at) = %s AND MONTH(writed_at) = %s"
            await cursor.execute(query, (member_id, date.year if date else None, date.month if date else None))
            result = await cursor.fetchall()
            feelings = [row['feeling'] for row in result]

        print(feelings)

        feeling_count = defaultdict(int)
        for feeling in feelings:
            feeling_count[feeling] += 1
            print(feeling_count)

        if feelings:
            max_feeling = max(feeling_count, key=feeling_count.get)
            print(max_feeling)
            feeling_count[max_feeling] = 0
            second_max_feeling = max(feeling_count, key=feeling_count.get)
            print(second_max_feeling)
        else:
            max_feeling = None
            second_max_feeling = None
            print(max_feeling)

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
    