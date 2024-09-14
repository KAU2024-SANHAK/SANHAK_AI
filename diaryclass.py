import enum as Enum
import requests
import json
from openai import OpenAI
import os
import prompt as Prompt
from dotenv import load_dotenv
from googleapiclient.discovery import build

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


class Diary:
    def __init__(self, member_id, created_at, updated_at, written_at):
        self.member_id = member_id
        self.created_at = created_at
        self.updated_at = updated_at
        self.written_at = written_at
        self.client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

    async def get_diary_data(self, attributes):
        return getattr(self, attributes, None)


class DiaryCompletion(Diary):
    def __init__(self, member_id, created_at, updated_at, written_at,
                 when, where, who, what, realized, feeling):
        super().__init__(member_id, created_at, updated_at, written_at)
        self.content = None
        self.title = None
        self.diary_data = {
            "when": when,
            "where": where,
            "who": who,
            "what": what,
            "realized": realized,
            "feeling": feeling
        }

    async def get_diary_completion(self):
        prompt = (Prompt.diary_complete_prompt %
                  (self.diary_data["when"],
                   self.diary_data["where"],
                   self.diary_data["who"],
                   self.diary_data["what"],
                   self.diary_data["realized"]))

        client = self.client
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": 'you are a diary writer'},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7
        )

        content = completion.choices[0].message.content
        lines = content.split('\n')

        # 첫 번째 줄을 title로, 나머지를 diary로 설정
        title = lines[0]
        diary = '\n'.join(lines[1:])

        self.content = diary
        self.title = title
        print(self.title)


class DiaryFeeling(Diary):
    def __init__(self, member_id, created_at, updated_at, written_at, content):
        super().__init__(member_id, created_at, updated_at, written_at)
        self.feeling = None
        self.content = content

    Feeling_Map = {
        "기쁨": "HAPPY",
        "슬픔": "SAD",
        "분노": "ANGRY",
        "걱정": "WORRIED",
        "놀람": "SURPRISED",
        "평온": "RELAX"
    }

    async def change_feeling(self, feeling):
        return self.Feeling_Map.get(feeling, None)

    async def get_diary_feeling(self):
        prompt = (Prompt.diary_feeling_prompt %
                  self.content)

        client = self.client
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": 'you are a diary writer'},
                {"role": "user", "content": prompt},
            ]
        )

        contents = completion.choices[0].message.content
        self.feeling = await self.change_feeling(contents)


class DiaryAdvice(Diary):
    def __init__(self, member_id, created_at, updated_at, written_at, content):
        super().__init__(member_id, created_at, updated_at, written_at)
        self.spicy_advice = None
        self.soft_advice = None
        self.content = content

    async def get_diary_advice(self):
        prompt = (Prompt.diary_advice_prompt %
                  self.content)

        client = self.client
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": 'you are a diary writer'},
                {"role": "user", "content": prompt},
            ]
        )

        content = completion.choices[0].message.content
        content = json.loads(content)

        self.spicy_advice = content['T comment']
        self.soft_advice = content['F comment']


class DiaryImage(Diary):
    def __init__(self, member_id, created_at, updated_at, written_at, content):
        super().__init__(member_id, created_at, updated_at, written_at)
        self.image = None
        self.content = content

    async def get_diary_image(self):
        prompts = Prompt.diary_image_prompt % self.content

        client = self.client
        completion = client.images.generate(
            model="dall-e-3",
            prompt=prompts,
            size="1024x1024",
            n=1
        )

        self.image = completion.data[0].url


class YoutubePlaylist():
    def __init__(self, content):
        self.youtube_api_key = os.environ['YOUTUBE_API_KEY']
        self.youtube_build = build('youtube', 'v3', developerKey=self.youtube_api_key)
        self.content = content
        self.playlist = None
        self.title = None
        self.thumbnail = None

    # 영어 감정을 한글로 변경하는 함수
    class Feeling(Enum.Enum):
        HAPPY = "기쁨"
        SAD = "슬픔"
        ANGRY = "분노"
        WORRIED = "걱정"
        SURPRISED = "놀람"
        RELAX = "평온"

    async def get_youtube_playlist(self):
        channel = "때껄룩ᴛᴀᴋᴇ ᴀ ʟᴏᴏᴋ"
        feeling = self.Feeling[self.content].value
        query = "%s, %s" % (feeling, channel)
        print(query)
        print(build)
        search_response = self.youtube_build.search().list(
            q=query,
            part="snippet",
            type='video',
            maxResults=1
        ).execute()

        for search_result in search_response.get("items", []):
            print(search_result)
            if search_result["id"]["kind"] == "youtube#video":
                self.playlist = f"https://www.youtube.com/watch?v={search_result['id']['videoId']}"
                self.title = search_result["snippet"]["title"]
                self.thumbnail = search_result["snippet"]["thumbnails"]["default"]["url"]
                print(self.playlist, self.title, self.thumbnail)
                break
        return self.playlist, self.title, self.thumbnail


class WeatherPlaylist(YoutubePlaylist):
    def __init__(self):
        super().__init__(None)
        self.city="Seoul"
        self.weather_api_key = os.environ['WEATHER_API_KEY']
        self.lang = "kr"
        self.api = f"""https://api.openweathermap.org/data/2.5/weather?q={self.city}&appid={self.weather_api_key}&lang={self.lang}&units=metric"""
        self.weather = requests.get(self.api)
        self.weather_json = json.loads(self.weather.text)
        self.current_weather = self.weather_json["weather"][0]["description"]
        self.icon = self.weather_json["weather"][0]["icon"]

    async def get_weather_playlist(self):
        print(self.weather_json)
        weather = self.current_weather

        channel = "때껄룩ᴛᴀᴋᴇ ᴀ ʟᴏᴏᴋ"
        query = "%s playlist" % weather
        print(query)
        print(self.youtube_build)
        search_response = self.youtube_build.search().list(
            q=query,
            part="snippet",
            type='video',
            maxResults=1
        ).execute()

        for search_result in search_response.get("items", []):
            print(search_result)
            if search_result["id"]["kind"] == "youtube#video":
                self.playlist = f"https://www.youtube.com/watch?v={search_result['id']['videoId']}"
                self.title = search_result["snippet"]["title"]
                self.thumbnail = search_result["snippet"]["thumbnails"]["default"]["url"]
                break
        return self.playlist, self.title, self.thumbnail


class ChuseokKeyword(Diary):
    def __init__(self, member_id, created_at, updated_at, written_at, content):
        super().__init__(member_id, created_at, updated_at, written_at)
        self.content = content
        self.keyword = None
        self.illustration = None

    keyword_map = {
        "송편": "송편 베어",
        "보름달": "보름달 베어",
        "한복": "한복 베어",
        "곶감": "곶감 베어",
        "집콕": "뒹굴 베어",
        "여행": "트레블 베어",
        "가족": "패밀리 베어"
    }

    illustration_map = {
        "송편 베어": "https://kkoolbee-storage.s3.ap-northeast-2.amazonaws.com/%EC%B6%94%EC%84%9D/%E1%84%8E%E1%85%AE%E1"
                 "%84%89%E1%85%A5%E1%86%A8+%E1%84%91%E1%85%A9%E1%86%AF%E1%84%83%E1%85%A5/%E1%84%89%E1%85%A9%E1%86%BC"
                 "%E1%84%91%E1%85%A7%E1%86%AB%E1%84%87%E1%85%A6%E1%84%8B%E1%85%A5.png",
        "보름달 베어": "https://kkoolbee-storage.s3.ap-northeast-2.amazonaws.com/%EC%B6%94%EC%84%9D/%E1%84%8E%E1%85%AE%E1"
                  "%84%89%E1%85%A5%E1%86%A8+%E1%84%91%E1%85%A9%E1%86%AF%E1%84%83%E1%85%A5/%E1%84%87%E1%85%A9%E1%84%85"
                  "%E1%85%B3%E1%86%B7%E1%84%83%E1%85%A1%E1%86%AF%E1%84%87%E1%85%A6%E1%84%8B%E1%85%A5.png",
        "한복 베어": "https://kkoolbee-storage.s3.ap-northeast-2.amazonaws.com/%EC%B6%94%EC%84%9D/%E1%84%8E%E1%85%AE%E1"
                 "%84%89%E1%85%A5%E1%86%A8+%E1%84%91%E1%85%A9%E1%86%AF%E1%84%83%E1%85%A5/%E1%84%92%E1%85%A1%E1%86%AB"
                 "%E1%84%87%E1%85%A9%E1%86%A8%E1%84%87%E1%85%A6%E1%84%8B%E1%85%A5.png",
        "곶감 베어": "https://kkoolbee-storage.s3.ap-northeast-2.amazonaws.com/%EC%B6%94%EC%84%9D/%E1%84%8E%E1%85%AE%E1"
                 "%84%89%E1%85%A5%E1%86%A8+%E1%84%91%E1%85%A9%E1%86%AF%E1%84%83%E1%85%A5/%E1%84%80%E1%85%A9%E1%86%BD"
                 "%E1%84%80%E1%85%A1%E1%86%B7%E1%84%87%E1%85%A6%E1%84%8B%E1%85%A5.png",
        "뒹굴 베어": "https://kkoolbee-storage.s3.ap-northeast-2.amazonaws.com/%EC%B6%94%EC%84%9D/%E1%84%8E%E1%85%AE%E1"
                 "%84%89%E1%85%A5%E1%86%A8+%E1%84%91%E1%85%A9%E1%86%AF%E1%84%83%E1%85%A5/%E1%84%8C%E1%85%B5%E1%86%B8"
                 "%E1%84%8F%E1%85%A9%E1%86%A8%E1%84%87%E1%85%A6%E1%84%8B%E1%85%A5.png",
        "트레블 베어": "hhttps://kkoolbee-storage.s3.ap-northeast-2.amazonaws.com/%EC%B6%94%EC%84%9D/%E1%84%8E%E1%85%AE%E1"
                  "%84%89%E1%85%A5%E1%86%A8+%E1%84%91%E1%85%A9%E1%86%AF%E1%84%83%E1%85%A5/%E1%84%90%E1%85%B3%E1%84%85"
                  "%E1%85%A6%E1%84%87%E1%85%B3%E1%86%AF%E1%84%87%E1%85%A6%E1%84%8B%E1%85%A5.png",
        "패밀리 베어": "https://kkoolbee-storage.s3.ap-northeast-2.amazonaws.com/%EC%B6%94%EC%84%9D/%E1%84%8E%E1%85%AE%E1"
                  "%84%89%E1%85%A5%E1%86%A8+%E1%84%91%E1%85%A9%E1%86%AF%E1%84%83%E1%85%A5/%E1%84%91%E1%85%A2%E1%84%86"
                  "%E1%85%B5%E1%86%AF%E1%84%85%E1%85%B5%E1%84%87%E1%85%A6%E1%84%8B%E1%85%A5.png"
    }


    async def change_keyword(self, keyword):
        return self.keyword_map.get(keyword, None)

    async def get_illustration(self, keyword):
        return self.illustration_map.get(keyword, None)

    async def get_chuseok_keyword(self):
        prompt = (Prompt.chuseok_keyword_prompt %
                  self.content)

        client = self.client
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": 'you are a diary writer'},
                {"role": "user", "content": prompt},
            ]
        )

        self.keyword = completion.choices[0].message.content
        self.keyword = await self.change_keyword(self.keyword)
        self.illustration = await self.get_illustration(self.keyword)