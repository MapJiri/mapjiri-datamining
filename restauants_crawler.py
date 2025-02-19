import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# 웹드라이버 설정
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

# 카카오맵 접속
driver.get("https://map.kakao.com/")

district = "장대동"
menu = "쌀국수"

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

        try:
            # 주소 크롤링
            address_full = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="mArticle"]/div[1]/div[2]/div[1]/div/span[1]'))
            ).text.strip()

            # 공백 기준으로 분할 후 앞 4개 단어만 가져오기
            address_parts = address_full.split()[:4]
            address_filtered = " ".join(address_parts)

        except:
            address_filtered = "주소 정보 없음"

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
                        "review_text": review_text,
                        "rating": rating,
                        "date": date,
                        "photo_url": photo_url,
                    })
                except:
                    continue
        except:
            reviews = None

        # 데이터 저장
        restaurants.append({
            "name": store_name,
            "place_name": address_filtered,
            "tag": tag_list,
            "reviews": reviews,
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

# JSON 저장
filename = f"{search_query.replace(' ', '_')}.json"
if restaurants:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(restaurants, f, ensure_ascii=False, indent=4)
else:
    print("저장할 데이터가 없습니다.")

# 드라이버 종료
driver.quit()
