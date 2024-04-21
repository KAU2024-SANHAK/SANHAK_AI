import enum as Enum
import datetime
import json
from openai import OpenAI
import os
import prompt as Prompt

class diary:
    '''class Feeling(Enum):
        HAPPY = 1
        SAD = 2
        ANGRY = 3
        WORRY = 4
        SURPRISED = 5
        RELAXED = 6'''
    class metadata:
        def __init__(self, member_id, created_at, updated_at, diarytype):
            self.member_id = member_id
            self.created_at = created_at
            self.updated_at = updated_at
            self.diarytype = diarytype

        def get_metadata(self, attributes):
            return getattr(self, attributes, None)

    class diary_content:
        def __init__(self, feeling, when, where, who, what, realized):
            self.feeling = feeling
            self.when = when
            self.where = where
            self.who = who
            self.what = what
            self.realized = realized
        def get_diary_content(self, attributes):
            return getattr(self, attributes, None)


    def __init__(self, diary_content, metadata, content, title, spicy_advice, soft_advice):
        self.diary_content = diary_content
        self.metadata = metadata
        self.content = content
        self.title = title
        self.spicy_advice = spicy_advice
        self.soft_advice = soft_advice
        self.client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

    def get_diary_data(self, attributes):
        if attributes in ["content", "title", "spicy_advice", "soft_advice", "client"]:
            return getattr(self, attributes, None)
        else:
            if attributes == "metadata":
                return self.metadata.get_metadata(attributes)
            else:
                return self.diary_content.get_diary_content(attributes)


    def get_diary_completion(self):

        prompt = (Prompt.diary_complete_prompt %
                  (self.get_diary_data("when"),
                   self.get_diary_data("where"),
                   self.get_diary_data("who"),
                   self.get_diary_data("what"),
                   self.get_diary_data("realized")))

        completion = self.get_diary_data("client").chat.completions.create(
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


    def is_feeling_empty(self):
        if self.get_diary_data("feeling") == None:
            return False
        else:
            return True

    def get_diary_feeling(self):
        prompt = (Prompt.diary_feeling_prompt % self.get_diary_data("content"))
        completion = self.get_diary_data("client").chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": 'you are a diary writer'},
                {"role": "user", "content": prompt},
            ]
        )

        content = completion.choices[0].message.content
        self.feeling = content

    def get_diary_advice(self):
        prompt = (Prompt.diary_advice_prompt % self.get_diary_data("content"))
        completion = self.get_diary_data("client").chat.completions.create(
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

