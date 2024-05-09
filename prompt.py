diary_complete_prompt = """
    유저가 제공한 정보:
- 언제: %s
- 어디서: %s
- 누구와: %s
- 무엇을: %s
- 느낀점: %s

다이어리 작성 지시:
유저가 제공한 '언제', '어디서', '누구와', '무엇을', '느낀점'에 바탕을 둔 일기를 작성하되, 
유저가 제공한 사실에 대한 추가 정보만을 포함하여 일기를 작성해 주세요.
유저의 느낀점을 중심으로, 그 경험이 유저에게 어떤 의미가 있었는지에 초점을 맞추어 진솔하게 작성해 주세요.
유저가 직접 언급하지 않은 새로운 사실이나 가정은 추가하지 마세요.

좋은 예시는 다음과 같습니다.
{
    - 언제: 2024년 4월 1일
    - 어디서: 제주도 한라산
    - 누구와: 친구들과
    - 무엇을: 한라산 등반
    - 느낀점: 산 정상에서 보는 풍경이 매우 인상적이었고, 함께 등반한 친구들과의 우정도 더 깊어진 기분이었다.

    - 완성된 다이어리의 예시 : 2024년 4월 1일, 친구들과 함께 제주도의 한라산을 등반했다.
    한라산은 한국에서 가장 높은 산으로, 그 정상에서 바라보는 제주도의 풍경은 정말로 인상적이였다.
    제주도의 파란 바다와 울창한 숲이 한눈에 들어왔고, 그 아름다움에 모두가 말을 잃었다.

    우리는 등반하면서 서로를 의지하며 많은 얘기를 나누었고, 함께 등반한 친구들과 나는 더욱 가까워진 것을 느꼈다.
    우리는 서로에 대해 더 많이 알게 되었고, 이 여행이 우리 사이의 우정을 더욱 깊게 만들었다는 것을 깨달았다.

    한라산 등반은 단순한 여행 이상의 의미가 있었다.
    이 경험은 나에게 자연의 아름다움을 다시 한번 일깨워 주었고, 친구들과의 관계를 더욱 소중히 여기게 만들었다.
    이번 등반을 통해 얻은 추억과 교훈은 앞으로도 오랫동안 내 마음속에 남아있을 것이다.
    }

    위의 예시처럼, 유저가 제공한 정보를 바탕으로 일기를 작성해주세요.
    추가로, 다른 추가적인 말은 덧붙여 제공하지 말고 완성된 다이어리 내용만 답변으로 제공해주세요.

    그리고 해당 일기의 제목을 10자 내로 작성하여 추가적인 말은 적지 말고 아래 형태로 반환해주세요.
    제목 : "제목의 내용" 과 같이 부가적인 말은 적지 말아주세요.
    오로지 제목과 완성된 다이어리 내용을 아래와 같이 반환해주세요.
    
    제목
    완성된 다이어리의 내용
    

    """


diary_feeling_prompt = """
유저의 diary 내용
- diary 내용: %s

유저의 diary 내용을 분석해 diary에서 확인할 수 있는 감정들을 분석해주세요.
분석을 하고 해당 감정이 나타나는 비율을 나타내주세요.
감정의 종류는 다음과 같습니다.
- 기쁨
- 평온
- 슬픔
- 분노
- 걱정
- 놀람

예시:
 - 다이어리 내용 예시 : 2024년 4월 1일, 친구들과 함께 제주도의 한라산을 등반했다.
    한라산은 한국에서 가장 높은 산으로, 그 정상에서 바라보는 제주도의 풍경은 정말로 인상적이였다.
    제주도의 파란 바다와 울창한 숲이 한눈에 들어왔고, 그 아름다움에 모두가 말을 잃었다.

    우리는 등반하면서 서로를 의지하며 많은 얘기를 나누었고, 함께 등반한 친구들과 나는 더욱 가까워진 것을 느꼈다.
    우리는 서로에 대해 더 많이 알게 되었고, 이 여행이 우리 사이의 우정을 더욱 깊게 만들었다는 것을 깨달았다.

    한라산 등반은 단순한 여행 이상의 의미가 있었다.
    이 경험은 나에게 자연의 아름다움을 다시 한번 일깨워 주었고, 친구들과의 관계를 더욱 소중히 여기게 만들었다.
    이번 등반을 통해 얻은 추억과 교훈은 앞으로도 오랫동안 내 마음속에 남아있을 것이다.

    - 분석 결과 예시 :
    {기쁨: 60, 놀람: 35, 슬픔: 5}
    
    단, 분석결과는 출력하지 말아주세요
    그리고 출력은 분석 결과에서 가장 높은 감정 한개만 출력해주세요
    추가적인 답변이나 말을 덧붙이지 말고 감정만 출력해주세요.
    예시 :
    기쁨
    """

diary_advice_prompt = """
유저의 diary 내용 : %s
유저의 diary 내용을 분석하여 유저에게 제공할 수 있는 답변을 작성해주세요.
답변은 두가지 유형으로 하나씩 작성합니다.
    1. MBTI "T"처럼 답변
    2. MBTI "F"처럼 답변

이때 답변은 인터넷을 찾아 정보를 주거나 인터넷을 차자 경험을 얘기해주는 것처럼 작성할 수 있어요.
일기 내용을 받고 일기에 대한 분석과 각 답변 유형별로 어떤 답변을 하면 좋을지 요청을 한 뒤에 이를 바탕으로 답변을 작성해주세요.

아래는 답변 예시입니다.
예시 :
    {
        일기 내용 예시 :
            오늘은 친구들과 함께 여의도 한강 공원에 갔다가 비가 와서 계획이 틀어졌다.
            나는 이 상황이 좀 답답했고, 친구들과의 관계도 어색해진 것 같아 속상하다. 
            다음에는 이런 상황이 발생하지 않도록 더 잘 준비하고 싶다.
            
        분석과 가이드라인 예시 : 
        {
            일기 분석: 사용자는 친구들과 함께 시간을 보내려 했지만, 예상치 못한 비로 인해 계획이 틀어지고, 그로 인해 친구들과의 관계가 어색해진 것에 대해 속상해하고 있다. 사용자는 이러한 상황을 미래에 더 잘 대비하고 싶어 한다.
    
            MBTI 'T' 유형에 맞는 답변 요청: 예상치 못한 상황에 대처하는 구체적이고 실용적인 조언을 제공해주세요.
    
            MBTI 'F' 유형에 맞는 답변 요청: 사용자의 감정과 공감을 바탕으로 한 답변을 제공해주세요. 명언을 활용하면 좋을 거 같아요.
        }
        답변 예시 :
            {
                MBTI 'T' 유형에 맞는 답변 : 
                    비가 올 가능성이 있는 날에는 항상 실내에서 할 수 있는 활동을 계획하는 것이 좋습니다. 
                    예를 들어, 여의도 쪽에는 박물관이나 아트 갤러리 방문, 카페에서의 티타임, 또는 집에서 영화 마라톤을 준비하는 것 등입니다. 
                    여의도 쪽에는 서울역사 박물관, IFC몰 MPX갤러리 혹은 더현대 등이 있으니 다음번 방문에는 이곳을 방문해보는 것도 좋을 것 같습니다.
                    또한, 모임 전에 날씨 예보를 확인하고, 비가 올 경우를 대비해 우산을 준비하거나 장소를 실내로 변경할 수 있는 옵션을 미리 생각해 두는 것이 중요합니다. 
                    이렇게 준비를 해두면, 예상치 못한 상황에도 친구들과 즐거운 시간을 보낼 수 있습니다.

    
                MBTI 'F' 유형에 맞는 답변 : 
                    예상치 못한 상황에 대처하는 방법으로는, 친구들과 솔직하게 대화를 나누어서 상황을 해결하는 것이 중요할 것 같아요. 
                    또한, 친구들과의 관계가 어색해진 것에 대해 속상해하는 마음을 친구들과 솔직하게 이야기하는 것이 좋을 것 같아요.
                    아일랜드 작가 오스카 와일드는 이렇게 말했어요 "궁극적으로 결혼이든 우정이든 관계에서 유대감을 형성하는 것은 대화다"
                    당신을 진정으로 아끼는 친구라면 당신의 솔직한 마음을 이해해줄거에요.
            }
    }
    
    결과물은 분석과 가이드라인은 제외하고 답변만  JSON 형태로 반환해주세요.
    
    아래는 반환 예시에요.
    {
    "T comment" : "비가 올 가능성이 있는 날에는 항상 실내에서 할 수 있는 활동을 계획하는 것이 좋습니다. 
                예를 들어, 박물관이나 아트 갤러리 방문, 카페에서의 티타임, 또는 집에서 영화 마라톤을 준비하는 것 등입니다. 
                여의도 쪽에는 서울역사 박물관, IFC몰 MPX갤러리 혹은 더현대 등이 있으니 다음번 방문에는 이곳을 방문해보는 것도 좋을 것 같습니다.
                또한, 모임 전에 날씨 예보를 확인하고, 비가 올 경우를 대비해 우산을 준비하거나 장소를 실내로 변경할 수 있는 옵션을 미리 생각해 두는 것이 중요합니다. 
                이렇게 준비를 해두면, 예상치 못한 상황에도 친구들과 즐거운 시간을 보낼 수 있습니다."
    
    "F comment" : "예상치 못한 상황에 대처하는 방법으로는, 친구들과 솔직하게 대화를 나누어서 상황을 해결하는 것이 중요할 것 같아요. 
                또한, 친구들과의 관계가 어색해진 것에 대해 속상해하는 마음을 친구들과 솔직하게 이야기하는 것이 좋을 것 같아요.
                아일랜드 작가 오스카 와일드는 이렇게 말했어요 "궁극적으로 결혼이든 우정이든 관계에서 유대감을 형성하는 것은 대화다"
                당신을 진정으로 아끼는 친구라면 당신의 솔직한 마음을 이해해줄거에요."
    }
"""