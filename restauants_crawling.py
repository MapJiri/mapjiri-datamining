import logging
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ✅ 로그 설정 (VS Code 터미널에서 실시간 확인 가능)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# ✅ 웹드라이버 설정 (크롬 창 표시)
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")  # 창 최대화
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920x1080")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=options)

# ✅ 카카오맵 접속
driver.get("https://map.kakao.com/")
logging.info("카카오맵 접속 완료")

# ✅ 검색 실행
input_tag = driver.find_element(By.ID, "search.keyword.query")
search_query = "대전 장대동 짜장면"
input_tag.send_keys(search_query)
input_tag.send_keys(Keys.RETURN)
time.sleep(2)
logging.info(f"검색 완료: {search_query}")

# ✅ "장소" 탭 클릭 (검색 후 정확한 가게 리스트 확인)
try:
    place_tab = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'li.option1 a'))
    )
    driver.execute_script("arguments[0].click();", place_tab)
    time.sleep(2)
    logging.info("장소 탭 클릭 완료")
except Exception as e:
    logging.error(f"장소 탭 클릭 실패: {e}")

# ✅ 크롤링 데이터 저장 리스트
restaurants = []

def scrape_restaurant():
    """가게 상세정보 및 모든 리뷰 크롤링"""
    try:
        driver.switch_to.window(driver.window_handles[1])
        time.sleep(2)  # 페이지 로딩 대기

        # ✅ 가게 이름 가져오기
        try:
            store_name = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="mArticle"]/div[1]/div[1]/div[2]/div/h2'))
            ).text.strip()
        except:
            store_name = "가게 정보 없음"

        logging.info(f"크롤링 시작: {store_name}")

        # ✅ "후기" 섹션으로 스크롤 이동
        try:
            review_section = driver.find_element(By.CLASS_NAME, "cont_evaluation")
            driver.execute_script("arguments[0].scrollIntoView();", review_section)
            time.sleep(1)
        except:
            logging.warning("후기 섹션을 찾을 수 없음")

        # ✅ "후기 더보기" 버튼 클릭 (후기 접기 나올 때까지 반복)
        while True:
            try:
                collapse_button = driver.find_elements(By.CSS_SELECTOR, "a.link_more.link_unfold")
                if collapse_button:
                    break  # "후기 접기"가 나오면 종료

                more_buttons = driver.find_elements(By.XPATH, '//*[@id="mArticle"]/div[8]/div[3]/a')
                if not more_buttons:
                    break  # 더 이상 버튼이 없으면 종료

                driver.execute_script("arguments[0].click();", more_buttons[0])
                time.sleep(2)  # 리뷰가 추가될 때까지 대기

            except Exception as e:
                logging.info("더 이상 '후기 더보기' 버튼이 없음")
                break  # 더 이상 버튼이 없으면 종료

        # ✅ 모든 리뷰가 로드될 때까지 대기
        review_elements = driver.find_elements(By.CSS_SELECTOR, "ul.list_evaluation > li")

        # ✅ 리뷰 크롤링 시작
        reviews = []
        for review in review_elements:
            try:
                review_text = review.find_element(By.CLASS_NAME, "txt_comment").text
                rating_style = review.find_element(By.CLASS_NAME, "inner_star").get_attribute("style")
                rating = rating_style.split("width:")[1].replace("%;", "").strip()
                date = review.find_element(By.CLASS_NAME, "time_write").text

                # ✅ 이미지 URL 가져오기
                try:
                    photo_element = review.find_element(By.CLASS_NAME, "list_photo").find_element(By.TAG_NAME, "img")
                    photo_url = photo_element.get_attribute("src")
                except:
                    photo_url = None

                reviews.append({
                    "review_text": review_text,
                    "rating": rating,
                    "date": date,
                    "photo_url": photo_url,
                })
            except:
                continue

        # ✅ 데이터 저장
        restaurants.append({
            "name": store_name,
            "reviews": reviews
        })
        logging.info(f"크롤링 완료: {store_name} (리뷰 수: {len(reviews)})")

        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        time.sleep(1)

    except Exception as e:
        logging.error(f"Error processing store: {e}")
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

# ✅ 1~5페이지 크롤링 실행
for current_page in range(1, 6):
    logging.info(f"{current_page}페이지 크롤링 시작")

    try:
        places = driver.find_elements(By.XPATH, '//*[@id="info.search.place.list"]/li')

        for place in places:
            try:
                details_button = place.find_element(By.CLASS_NAME, "moreview")
                driver.execute_script("arguments[0].click();", details_button)
                time.sleep(2)
                scrape_restaurant()
            except:
                continue

        # ✅ 다음 페이지 이동 (5페이지까지만 이동)
        if current_page < 5:
            try:
                next_page_button = driver.find_element(By.ID, f"info.search.page.no{current_page + 1}")
                driver.execute_script("arguments[0].click();", next_page_button)
                time.sleep(2)
            except:
                logging.info(f"{current_page} 페이지 이동 실패 또는 마지막 페이지 도달")
                break

    except Exception as e:
        logging.error(f"Error during pagination: {e}")
        break

# ✅ JSON 저장
json_filename = "daejun_restaurants_reviews.json"
with open(json_filename, "w", encoding="utf-8") as json_file:
    json.dump(restaurants, json_file, ensure_ascii=False, indent=4)

logging.info(f"✅ JSON 저장 완료: {json_filename}")

# ✅ 드라이버 종료
driver.quit()
logging.info("크롤링 완료")
