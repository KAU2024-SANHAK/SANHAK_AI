import enum as Enum
import datetime
import json
from openai import OpenAI
import os
import prompt as Prompt
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


class diary:
    async def change_feeling(self, feeling):
        feelings = {"기쁨": "HAPPY", "슬픔": "SAD", "분노": "ANGRY", "걱정": "WORRIED", "놀람": "SURPRISED", "평온": "RELAX"}.get(
            feeling, None)
        return feelings

    class metadata:
        def __init__(self, member_id, created_at, updated_at, diarytype):
            self.member_id = member_id
            self.created_at = created_at
            self.updated_at = updated_at
            self.diarytype = diarytype

        async def get_metadata(self, attributes):
            return getattr(self, attributes, None)

    class diary_content:
        def __init__(self, feeling, when, where, who, what, realized):
            self.feeling = feeling
            self.when = when
            self.where = where
            self.who = who
            self.what = what
            self.realized = realized

        async def get_diary_content(self, attributes):
            return getattr(self, attributes, None)

    def __init__(self, diary_content, metadata, content, title, spicy_advice, soft_advice, feelings):
        self.diary_content = diary_content
        self.metadata = metadata
        self.content = content
        self.title = title
        self.spicy_advice = spicy_advice
        self.soft_advice = soft_advice
        self.feelings = feelings
        self.client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

    async def get_diary_data(self, attributes):
        if attributes in ["content", "title", "spicy_advice", "soft_advice", "client", "feelings"]:
            return getattr(self, attributes, None)
        else:
            if attributes in ["member_id", "created_at", "updated_at", "diarytype"]:
                return await self.metadata.get_metadata(attributes)
            else:
                return await self.diary_content.get_diary_content(attributes)


    async def get_diary_completion(self):

        prompt = (Prompt.diary_complete_prompt %
                  (await self.get_diary_data("when"),
                   await self.get_diary_data("where"),
                   await self.get_diary_data("who"),
                   await self.get_diary_data("what"),
                   await self.get_diary_data("realized")))

        client = await self.get_diary_data("client")
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": 'you are a diary writer'},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=500
        )

        content = completion.choices[0].message.content
        lines = content.split('\n')

        # 첫 번째 줄을 title로, 나머지를 diary로 설정
        title = lines[0]
        diary = '\n'.join(lines[1:])

        self.content = diary
        self.title = title
        self.updated_at = datetime.datetime.now().isoformat()


    async def get_diary_feeling(self):
        prompt = (Prompt.diary_feeling_prompt % await self.get_diary_data("content"))

        client = await self.get_diary_data("client")
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": 'you are a diary writer'},
                {"role": "user", "content": prompt},
            ]
        )

        content = completion.choices[0].message.content
        self.feelings = await self.change_feeling(content)

    async def get_diary_advice(self):
        prompt = (Prompt.diary_advice_prompt % await self.get_diary_data("content"))

        client = await self.get_diary_data("client")
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
