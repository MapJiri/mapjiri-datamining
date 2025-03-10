# 🗺️ Mapjiri 🗺️

```
 카카오지도 API를 활용한 리뷰(후기) 관리, Mapjiri
```

<br/>

## 🧑‍💻 Mapjiri Crawling Cloud Developers
| 김승진 |
| :---: | 
| <img width="250" alt="branch" src="https://github.com/user-attachments/assets/321f6779-951d-417a-91e8-6ae905ac87ae"> | 
| [Kimseungjin0529](https://github.com/Kimseungjin0529) |
| 서버에서 기존 크롤링 로직 분리 <br> 크롤링 자동화 <br> AWS 서버 구축 <br> Lambda, SQS, EventBridge, s3 등|


<br/>

### 🌳 프로젝트 요구 사항
- 카카오지도 API를 활용하여 주소별 사용자 리뷰(후기) 데이터를 체계적으로 정리 및 분석합니다.
- 리뷰(후기) 데이터를 활용하여 사용자에게 맞춤형 정보를 제공하며, 데이터 기반의 비즈니스 의사결정에 기여할 수 있는 플랫폼을 구축합니다.

<br/> 

### 🌳 흐름
<img width="590" alt="image" src="https://github.com/user-attachments/assets/ef8f63eb-60dc-460b-9e12-a56054cb2c95" />
<br/> 

#### 🚩 문제 사항
- 구현에 있어 카카오지도 API를 활용하여 주소별 사용자 리뷰(후기) 데이터를 체계적으로 정리 및 분석하는 것이 필수 사항으로 요구함
- 하지만 역설적이게 카카오지도 API에서는 주소별 사용자 리뷰(후기) 데이터를 제공하는 API를 제공하지 않음

#### ✅ 해결 방안
- 카카오지도에서 직접 검색해서 리뷰(후기) 데이터를 수집하는 기능 필요 -> 크롤링을 통해 해결

#### ❗️ 개선 요소
- 요소1. 주소별 사용자 리뷰(후기) 데이터를 크롤링해서 수집하기엔 검색 키워드로 나오는 주소가 너무 많음 (ex : 서울 맛집, 대전 대덕구 중식, 부산 풀코스 등)
- 요소2. 수동 크롤링 수행 -> 데이터 처리 과정에 소요되는 시간이 크고 무궁무진한 검색 키워드로 수동로 리뷰(후기) 데이터를 가공하는 것은 불가능에 가까움
- 요소3. 리뷰(후기) 데이터는 주소별 가게에 따라 뷸규칙적 가변성을 지님 -> 사용자에게 과거 정보를 제공할 수 있음

#### 🟢 개선
- 요소1 개선. 특정 지역(대전)의 모든 행정동(대덕동, .. 등) * 음식 키워드 리스트[ex) 중식 : 짜장, 짬뽕, .. / 일식 : 초밥, 튀김, ...등] 조합으로 최대한 많은 정보 제공
- 요소2 개선. 조합된 키워드[ex) 대전 대덕동 짜장] 별로 크롤링 자동화 
- 요소3 개선. trade-off를 고려한 특정 주기마다(1일, 3일, 1주일 등) 크롤링하여 최신 정보 제공
<br/> 

### 참고/정리 링크
[AWS Lambda 활용기](https://radical-ocean-d1e.notion.site/AWS-Lambda-1a1fb93e052980f0a51bf864273b130b)



### 📁 Foldering
```
.
├── 🗂️crawling
│   ├── 🗂️basic
│   │   ├── Dockerfile
│   │   ├── chrome-deps.txt
│   │   ├── install-browser.sh
│   │   ├── main.py
│   │   └── requirements.txt
│   ├── formatted_keywords.json
│   └── 🗂️test
│       ├── Dockerfile
│       ├── chrome-deps.txt
│       ├── install-browser.sh
│       ├── main.py
│       └── requirements.txt
├── 🗂️daejeon
│   ├── daejeonDaedeokgu.py
│   ├── daejeonDonggu.py
│   ├── daejeonJunggu.py
│   ├── daejeonSeogu.py
│   ├── daejeonYueseonggu.py
│   ├── 대전광역시_대덕구_행정동.csv
│   ├── 대전광역시_동구_행정동.csv
│   ├── 대전광역시_서구_행정동.csv
│   ├── 대전광역시_유성구_행정동.csv
│   └── 대전광역시_중구_행정동.csv
├── 🗂️menu
│   └── 메뉴.csv
└── restauants_crawler.py


```



<br/>

## 🛠️ Tech Stack
| 사용기술               | 정보                            |
|--------------------|-------------------------------|
| python             | 3.9                         |
| selenium           | Lastest                |
| chorem driver           | *                 |
| aws event bridge           | *               |
| aws lambda	             | container image function |
| aws sqs         | *                        |
| aws s3         | *                        |




<br/>

## 🔨 Architecture Flow
<img width="1099" alt="image" src="https://github.com/user-attachments/assets/49bcf3bf-0936-4210-800d-b54f94ca5f70" />




```````
