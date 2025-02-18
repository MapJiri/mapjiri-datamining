import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import requests  #  API 요청을 위한 라이브러리 
import boto3  # AWS SQS 메시지 처리를 위한 라이브러리 


sqs = boto3.client("sqs")
SQS_QUEUE_URL = "https://sqs.ap-northeast-2.amazonaws.com/182399700501/crawling_keyword"
API_URL = "http://13.124.190.196:8080/api/v1/restaurant/info"

def handler(event=None, context=None):
    # 📌 SQS 메시지 가져오기
    response = sqs.receive_message(
        QueueUrl=SQS_QUEUE_URL,
        MaxNumberOfMessages=1,  
        WaitTimeSeconds=10  
    )
    # 📌 메시지가 없을 경우 처리
    if "Messages" not in response:
        print("📌 처리할 메시지가 없습니다.")
        return {"statusCode": 400, "body": json.dumps("No messages to process")}

    # SQS 메시지에서 데이터 가져오기
    message = response["Messages"][0]
    receipt_handle = message["ReceiptHandle"]

    keyword_data = json.loads(message["Body"])  # {"dong": "오정동", "keyword": "파스타"}
    district = keyword_data.get("dong", "기본동")  # 기본값 설정
    menu = keyword_data.get("keyword", "기본메뉴")
    


    # 웹드라이버 설정
    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = "/opt/chrome/chrome"
    chrome_options.add_argument("--headless")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--single-process")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko")
    chrome_options.add_argument('window-size=1392x1150')
    chrome_options.add_argument("disable-gpu")
    chrome_options.add_argument("--start-maximized")
    service = Service(executable_path="/opt/chromedriver")

    driver = webdriver.Chrome(service=service, options=chrome_options)

    # 카카오맵 접속
    driver.get("https://map.kakao.com/")
    search_query = f"대전 {district} {menu}"
    
    # 검색 실행
    input_tag = driver.find_element(By.ID, "search.keyword.query")
    input_tag.send_keys(search_query)
    input_tag.send_keys(Keys.RETURN)
    time.sleep(2)

    # '장소 더보기' 버튼 클릭
    try:
        more_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "info.search.place.more")))
        driver.execute_script("arguments[0].click();", more_button)
        time.sleep(3)
    except:
        pass

    # '1페이지' 버튼 클릭
    try:
        first_page_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "info.search.page.no1")))
        driver.execute_script("arguments[0].click();", first_page_button)
        time.sleep(3)
    except:
        pass

    # 크롤링 데이터 저장 리스트
    restaurants = []

    def scrape_restaurant():
        """가게 상세정보 크롤링"""
        try:
            driver.switch_to.window(driver.window_handles[1])

            # 가게 이름
            try:
                store_name = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="mArticle"]/div[1]/div[1]/div[2]/div/h2'))
                ).text.strip()
            except:
                store_name = "가게 정보 없음"

            # 가게 주소명
            try:
                place_name = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="mArticle"]/div[1]/div[2]/div[1]/div/span[1]'))
                ).text.strip()
            except:
                place_name = "주소 정보 없음"

            # 추천 포인트 크롤링
            try:
                tag_list = {}
                like_points = driver.find_elements(By.CSS_SELECTOR, ".view_likepoint .chip_likepoint")
                for point in like_points:
                    key = point.find_element(By.CLASS_NAME, "txt_likepoint").text.strip()
                    value = point.find_element(By.CLASS_NAME, "num_likepoint").text.strip()
                    tag_list[key] = value
            except:
                tag_list = {}

            # 모든 리뷰 크롤링
            reviews = []
            try:
                while True:
                    try:
                        # 더보기 버튼 찾기
                        try:
                            more_button = driver.find_element(By.XPATH, '//*[@id="mArticle"]/div[8]/div[3]/a')
                        except:
                            try:
                                more_button = driver.find_element(By.XPATH, '//*[@id="mArticle"]/div[7]/div[3]/a')
                            except:
                                more_button = None

                        if more_button:
                            if "후기 접기" in more_button.text:
                                break
                            driver.execute_script("arguments[0].click();", more_button)
                            time.sleep(2)
                        else:
                            break
                    except:
                        break

                review_elements = driver.find_elements(By.CSS_SELECTOR, "ul.list_evaluation > li")
                for review in review_elements[:50]:
                    try:
                        review_text = review.find_element(By.CLASS_NAME, "txt_comment").text
                        rating_style = review.find_element(By.CLASS_NAME, "inner_star").get_attribute("style")
                        rating = rating_style.split("width:")[1].replace("%;", "").strip()
                        date = review.find_element(By.CLASS_NAME, "time_write").text

                        # 이미지 URL 가져오기
                        try:
                            photo_element = review.find_element(By.CLASS_NAME, "list_photo").find_element(By.TAG_NAME, "img")
                            photo_url = photo_element.get_attribute("src")
                        except:
                            photo_url = None

                        reviews.append({
                            "reviewText": review_text,
                            "rating": rating,
                            "date": date,
                            "photoUrl": photo_url,
                        })
                    except:
                        continue
            except:
                reviews = None

            # 데이터 저장
            restaurants.append({
                "name": store_name,
                "address": place_name,
                "tags": tag_list,
                "reviews": reviews
            })

            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            time.sleep(2)

        except:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

    # 최대 페이지 수 확인
    try:
        pagination = driver.find_elements(By.XPATH, '//div[@id="info.search.page"]//a[contains(@id, "info.search.page.no")]')
        page_numbers = [int(p.text.strip()) for p in pagination if p.text.strip().isdigit()]
        max_page = max(page_numbers) if page_numbers else 1
    except:
        max_page = 1

    # 최대 3페이지까지만 크롤링 제한
    max_page = min(max_page, 3)

    # 1~max_page 페이지 크롤링
    for current_page in range(1, max_page + 1):
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, '//*[@id="info.search.place.list"]/li'))
            )
            places = driver.find_elements(By.XPATH, '//*[@id="info.search.place.list"]/li')

            for place in places:
                try:
                    details_button = place.find_element(By.CLASS_NAME, "moreview")
                    driver.execute_script("arguments[0].click();", details_button)
                    time.sleep(3)
                    scrape_restaurant()
                except:
                    continue

            # 다음 페이지 이동
            if current_page < max_page:
                try:
                    next_page_button = driver.find_element(By.ID, f"info.search.page.no{current_page + 1}")
                    driver.execute_script("arguments[0].click();", next_page_button)
                    time.sleep(3)
                except:
                    break
        except:
            break

    # 드라이버 종료
    driver.quit()

    # 📌 API 요청 데이터 생성
    request_body = {"list": restaurants}
    headers = {"Content-Type": "application/json"}

    # 📌 API 호출
    try:
        response = requests.post(API_URL, headers=headers, json=request_body)
        response_data = response.json()
        print(f"📌 API 응답: {response.status_code}, 내용: {response_data}")

            # 📌 SQS 메시지 삭제 (성공적으로 처리된 경우)
        sqs.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=receipt_handle)
        print(f"✅ SQS 메시지 삭제 완료: {district} - {menu}")

    except Exception as e:
        print(f"🚨 API 요청 실패: {str(e)}")

    # JSON 데이터 직접 반환
    return {
        "statusCode": 200,
        "body": json.dumps(restaurants, ensure_ascii=False, indent=4)
    }

if __name__ == '__main__':
    handler()