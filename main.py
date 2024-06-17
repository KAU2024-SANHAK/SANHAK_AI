import aiomysql
import traceback
import datetime
import diaryclass as diary
from collections import defaultdict
from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response
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
        return Response(status_code=500, content="MySQL 연결에 실패했습니다.")
    data = await request.json()
    member_id = request.headers.get('Authorization')

    if member_id is None:
        return Response(status_code=401, content="토큰이 없습니다.")

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
            content=new_diary.content
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
            image = None
            query = ("INSERT INTO diary (`title`, `content`, `writed_at`,`created_at`,"
                     "`updated_at`, `feeling`, `member_id`, `imageurl`) "
                     "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)")
            await cursor.execute(query, (title, content, writed_at, created_at,
                                         updated_at, feeling, member_id, image))
            diary_id = cursor.lastrowid

            await conn.commit()

            # diary_id와 diaryContent가 null 값인지 확인하여 처리합니다.
        diary_id = diary_id if diary_id is not None else 0


    except Exception as e:
        error_message = str(e)
        traceback_message = traceback.format_exc()
        return Response(status_code=500, content="요청이 실패했습니다.")

    finally:
        conn.close()

    return {
            "status": 201,
            "message": "요청이 성공했습니다.",
            "data": {
                "diaryId": diary_id,
                "title": title,
                "diaryContent": content,
                "feeling": feeling,
                "writed_at": writed_at,
                "imageurl": image
            }
    }


@app.post('/api/ai/diary/feeling')
async def get_diary_feelings(request: Request):
    conn = await connect_mysql()
    if conn is None:
        return Response(status_code=500, content="MySQL 연결에 실패했습니다.")
    data = await request.json()
    member_id = request.headers.get('Authorization')
    dairy_id = data.get('diaryId')

    print(member_id, dairy_id)
    if member_id is None:
        return Response(status_code=401, content="토큰이 없습니다.")

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
            return Response(status_code=400, content="감정을 분석할 수 없습니다.")
        print(feelings)

        async with conn.cursor() as cursor:
            query = "UPDATE diary SET feeling = %s WHERE member_id = %s AND diary_id = %s"
            await cursor.execute(query, (feelings, member_id, dairy_id))
        await conn.commit()

    except Exception as e:
        error_message = str(e)
        traceback_message = traceback.format_exc()
        return Response(status_code=500, content="요청이 실패했습니다.")
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
        return Response(status_code=500, content="MySQL 연결에 실패했습니다.")
    data = await request.json()
    member_id = request.headers.get('Authorization')
    dairy_id = data.get('diaryId')

    if member_id is None:
        return Response(status_code=401, content="토큰이 없습니다.")

    if dairy_id is None:
        return Response(status_code=400, content="일기 ID가 없습니다.")

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
        return Response(status_code=500, content="요청이 실패했습니다.")

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
        return Response(status_code=500, content="MySQL 연결에 실패했습니다.")

    member_id = request.headers.get('Authorization')
    date = datetime.datetime.now()

    if member_id is None:
        return Response(status_code=401, content="토큰이 없습니다.")

    try:
        async with conn.cursor() as cursor:
            ## 주어진 date에 해당하는 년도와 해당 월에 작성된 일기의 감정을 분석
            query = "SELECT feeling FROM diary WHERE member_id = %s AND YEAR(writed_at) = %s AND MONTH(writed_at) = %s"
            await cursor.execute(query, (member_id, date.year if date else None, date.month if date else None))
            result = await cursor.fetchall()
            feelings = [row['feeling'] for row in result]

        feeling_count = defaultdict(int)
        for feeling in feelings:
            feeling_count[feeling] += 1

        if feelings:
            max_feeling = max(feeling_count, key=feeling_count.get)
            feeling_count[max_feeling] = 0
            second_max_feeling = max(feeling_count, key=feeling_count.get)
        else:
            max_feeling = None
            second_max_feeling = None

    except Exception as e:
        error_message = str(e)
        traceback_message = traceback.format_exc()
        return Response(status_code=500, content="요청이 실패했습니다.")

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


@app.post('/api/ai/diary/image')
async def get_diary_image(request: Request):
    conn = await connect_mysql()
    if conn is None:
        return Response(status_code=500, content="MySQL 연결에 실패했습니다.")
    member_id = request.headers.get('Authorization')
    data = await request.json()
    dairy_id = data.get('diaryId')

    if member_id is None:
        return Response(status_code=401, content="토큰이 없습니다.")

    if dairy_id is None:
        return Response(status_code=400, content="일기 ID가 없습니다.")

    try:
        async with conn.cursor() as cursor:
            query = "SELECT content FROM diary WHERE member_id = %s AND diary_id = %s"
            await cursor.execute(query, (member_id, dairy_id))
            content = await cursor.fetchone()
            content = content['content']

        new_image = diary.DiaryImage(
            member_id=member_id,
            created_at=None,
            updated_at=None,
            written_at=None,
            content=content
        )

        await new_image.get_diary_image()

        image = new_image.image

        async with conn.cursor() as cursor:
            query = "UPDATE diary SET imageurl = %s WHERE member_id = %s AND diary_id = %s"
            await cursor.execute(query, (image, member_id, dairy_id))
        await conn.commit()

    except Exception as e:
        error_message = str(e)
        traceback_message = traceback.format_exc()
        return Response(status_code=500, content="요청이 실패했습니다.")

    finally:
        conn.close()

    return {
        "status": 201,
        "message": "요청이 성공했습니다.",
        "data": {
            "diaryId": dairy_id,
            "image_url": image
        }
    }


@app.post('/api/diary/youtube')
async def get_youtube_playlist(request: Request):

    data = await request.json()
    member_id = request.headers.get('Authorization')

    if member_id is None:
        return Response(status_code=401, content="토큰이 없습니다.")

    feeling = data.get('month feeling 1', None)
    if feeling is None:
        feeling = data.get('month feeling 2', None)

    new_playlist = diary.YoutubePlaylist(
        content=feeling
    )

    # await new_playlist.get_youtube_playlist()

    playlist_url = 'https://youtu.be/Ddk3_Oh0dw8?si=p4o8-VDrl3Em954H'
    # new_playlist.playlist
    title = '𝐏𝐥𝐚𝐲𝐥𝐢𝐬𝐭 빡쳐서 주체가 안 되면 일단 들어와 봐'
    # new_playlist.title
    thumbnail = 'https://kkoolbee-storage.s3.ap-northeast-2.amazonaws.com/8ec2e675b4d9d0ed37df7b7553b234a47295f5002aa0053b9a8574ec5e637fa7-image-12261246255767363184.png'
    # new_playlist.thumbnail

    return {
        "status": 200,
        "message": "요청이 성공했습니다.",
        "data": {
            "title": title,
            "playlist_url": playlist_url,
            "thumbnail": thumbnail
        }
    }


@app.get('/api/playlist/weather')
async def get_weather_playlist(request: Request):
    member_id = request.headers.get('Authorization')

    if member_id is None:
        return Response(status_code=401, content="토큰이 없습니다.")

    new_playlist = diary.WeatherPlaylist()

    # await new_playlist.get_weather_playlist()

    playlist_url = 'https://youtu.be/xgleSFQ3cLo?si=UhY8u537Aq1ufPaS'
    # new_playlist.playlist
    title = '𝐏𝐥𝐚𝐲𝐥𝐢𝐬𝐭 벌써 여름이야, 시원하고 청량한 음악 담아왔어'
    # new_playlist.title
    thumbnail = 'https://kkoolbee-storage.s3.ap-northeast-2.amazonaws.com/09068c885fdd5ceeb51b8b4f0c23c2a127c5c1d7f69b17f054766823c7f98823-image-3126367375241923998.png'
    # new_playlist.thumbnail
    weather = new_playlist.current_weather
    icon = "https://openweathermap.org/img/wn/%s@2x.png" % new_playlist.icon

    return {
        "status": 200,
        "message": "요청이 성공했습니다.",
        "data": {
            "title": title,
            "playlist_url": playlist_url,
            "thumbnail": thumbnail,
            "weather": weather,
            "icon": icon
        }
    }


if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=8080)
    