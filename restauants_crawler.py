from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd

# 웹드라이버 설정
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")  # 창 최대화
driver = webdriver.Chrome(options=options)

# 카카오맵 접속
driver.get("https://map.kakao.com/")

# 검색 실행
input_tag = driver.find_element(By.ID, "search.keyword.query")

search_query = "대전 장대동 짜장면"
input_tag.send_keys(search_query)
input_tag.send_keys(Keys.RETURN)

# 가게 정보 크롤링
restaurants = []

# 페이지 로딩 대기
WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "placelist")))
time.sleep(3)

for current_page in range(1, 4):  # 1페이지부터 5페이지까지 크롤링
    try:
        print(f"현재 페이지: {current_page}")

        # 현재 페이지에서 모든 가게 크롤링
        places = driver.find_elements(By.XPATH, '//*[@id="info.search.place.list"]/li')

        for place in places:
            try:
                # 상세보기 버튼 클릭 (새 탭에서 열기)
                details_button = place.find_element(By.CLASS_NAME, "moreview")
                driver.execute_script("arguments[0].click();", details_button)
                time.sleep(3)

                # 새 탭으로 이동
                driver.switch_to.window(driver.window_handles[1])

                # 가게 상세 이름 크롤링
                try:
                    store_name = driver.find_element(By.XPATH, '//*[@id="mArticle"]/div[1]/div[1]/div[2]/div/h2').text.strip()
                except:
                    store_name = "가게 정보 없음"  # 가져오지 못하면 기본 값으로 설정

                # 시설 정보 가져오기
                try:
                    facility_info = driver.find_element(By.CLASS_NAME, "placeinfo_facility").text
                except:
                    facility_info = "시설 정보 없음"

                try:
                    tag_elements = driver.find_elements(By.CLASS_NAME, "chip_likepoint")
                    tag_list = []

                    for tag in tag_elements:
                        tag_name = tag.find_element(By.CLASS_NAME, "txt_likepoint").text.strip()  # 태그 이름 (예: "맛")
                        tag_count = tag.find_element(By.CLASS_NAME, "num_likepoint").text.strip()  # 태그 숫자 (예: "7")

                        tag_list.append([tag_name, tag_count])

                except Exception as e:
                    tag_list = []

                # 모든 리뷰 불러오기
                reviews = []
                try:
                    while True:
                        try:
                            more_button = driver.find_element(By.XPATH, '//*[@id="mArticle"]/div[8]/div[3]/a')
                            if "후기 접기" in more_button.text:  # '후기 접기'가 되면 종료
                                break
                            more_button.click()
                            time.sleep(2)
                        except:
                            break  # 더 이상 리뷰가 없으면 종료

                    # 모든 리뷰 수집
                    review_elements = driver.find_elements(By.CSS_SELECTOR, "ul.list_evaluation > li")
                    for review in review_elements[:50]:
                        try:
                            review_text = review.find_element(By.CLASS_NAME, "txt_comment").text  # 리뷰 내용
                            rating_style = review.find_element(By.CLASS_NAME, "inner_star").get_attribute("style")
                            rating = rating_style.split("width:")[1].replace("%;", "").strip()  # 별점 변환
                            date = review.find_element(By.CLASS_NAME, "time_write").text  # 작성일

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

                # 데이터 저장 (CSV에 정상적으로 저장되도록 리스트에 추가)
                restaurants.append({
                    "name": store_name,
                    "facility_info": facility_info,
                    "tag": tag_list,
                    "reviews": reviews
                })

                # 새 탭 닫고 원래 탭으로 복귀
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                time.sleep(2)

            except Exception as e:
                print(f"Error on store: {e}")
                continue

        # 페이지 번호 클릭 (1~3)
        if current_page < 4:
            try:
                page_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, f"info.search.page.no{current_page + 1}"))
                )
                driver.execute_script("arguments[0].click();", page_button)
                time.sleep(5)  # 페이지 로딩 대기
            except:
                print(f"{current_page + 1} 페이지로 이동 실패.")
                break

    except Exception as e:
        print(f"Error during pagination: {e}")
        break

# CSV 파일 저장 (정상적으로 저장되도록 `restaurants` 리스트를 데이터프레임으로 변환)
df = pd.DataFrame(restaurants)

# CSV 파일이 빈 데이터가 아닌지 확인
if not df.empty:
    df.to_csv("대전 장대동 짜장면.csv", index=False, encoding="utf-8-sig")
    print("CSV 저장 완료: 대전 장대동 짜장면.csv")
else:
    print("저장할 데이터가 없습니다.")

# 드라이버 종료
driver.quit()
print("크롤링 완료.")
