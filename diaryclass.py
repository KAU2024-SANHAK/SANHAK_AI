import enum as Enum
import datetime
import json
from openai import OpenAI
import os
import prompt as Prompt
from dotenv import load_dotenv
from abc import ABC, abstractmethod

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
            model="gpt-4",
            messages=[
                {"role": "system", "content": 'you are a diary writer'},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=450
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
            model="gpt-4",
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
            model="gpt-4",
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
        prompts = Prompt.diary_image_prompt.format(self.content)

        client = self.client
        completion = client.images.generate(
            model="dall-e-3",
            prompt=prompts,
            size="1024x1024",
            n=1
        )

        self.image = completion.data[0].url
