""" 
# joywins_my_data_coupang_order

## 쿠팡 주문 목록 스크래퍼

### 라이선스

MIT License

### 개요

- 사용자의 쿠팡 '주문목록' 데이터를 사용자 로그인 후 자동으로 추출하여 CSV 파일로 저장하는 도구입니다.


### 기능

- 사용자 로그인 후 '주문목록' 데이터 자동 스크래핑
- 날짜 범위 지정 가능
- 주문 날짜, 상품명, 가격, URL, 주문 상태, 분리 배송 여부 등의 정보 스크래핑
- CSV 형식으로 데이터 저장


### 설치

> pip install joywins_my_data_coupang_order


### 사용법

1. 터미널에서 명령을 실행하면 크롬 웹브라우저가 열리고 쿠팡 로그인 페이지로 이동합니다.
2. 사용자가 30초 내에 쿠팡 웹사이트에 직접 로그인합니다.
3. 로그인이 완료되면 자동으로 주문 목록 스크래핑이 시작됩니다.
4. 스크래핑이 완료되면 CSV 파일로 저장됩니다.

### 예시
```
from joywins_my_data_coupang_order import joywins_my_data_coupang_order as my_data

if __name__ == "__main__":    
    my_data.get()  # 전체 주문 목록 조회  
    # my_data.get("2024.08.13")  # 2024.08.13 일자의 주문 목록 조회
    # my_data.get(["2024.08.30", ])  # 2024.08.30 부터 현재까지 주문 목록 조회
    # my_data.get([None, "2024.07.06"])  # 처음부터 2024.07.06 까지 주문 목록 조회
    # my_data.get(["2024.09.02", "2024.10.04"])  # 특정 기간의 주문 목록 조회    
```


### 주의 사항

- 쿠팡 로그인 페이지로 이동 후 30초 내에 사용자가 직접 수동으로 쿠팡 웹사이트에 로그인해야 합니다.
- 쿠팡 웹사이트의 구조 변경에 따라 스크래핑 코드가 작동하지 않을 수 있습니다.
- 쿠팡 이용 약관을 준수하여 사용해야 합니다.
"""

import sys

import time
import datetime

import csv
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from fake_useragent import UserAgent
from bs4 import BeautifulSoup

# --- 상수 정의 ---
LOGIN_TIMEOUT = 30
SCRAPING_TIMEOUT = 10


# --- 함수 정의 ---
def get_random_desktop_user_agent():
    """랜덤한 데스크탑 User-Agent를 반환"""
    ua = UserAgent()
    while True:
        user_agent = ua.random
        if "Mobi" not in user_agent and "Android" not in user_agent:
            return user_agent


def setup_driver():
    """Selenium WebDriver를 설정"""
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument(f"user-agent={get_random_desktop_user_agent()}")
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("detach", True)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # 크롬 웹브라우저 비밀번호 저장 팝업 비활성화
    options.add_experimental_option("prefs", {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    })

    driver = webdriver.Chrome(options=options)
    
   
    # navigator.webdriver 숨기기
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
    })
    
    return driver


"""
p_by: By.CSS_SELECTOR
"""
def find_element(p_driver, p_ec, p_by, p_selector, timeout=10):
    """요소를 찾아 반환"""
    wait = WebDriverWait(p_driver, timeout)
    
    if p_ec == "clickable":
        return wait.until(EC.element_to_be_clickable((p_by, p_selector)))
    elif p_ec == "visibility":
        return wait.until(EC.visibility_of_element_located((p_by, p_selector)))
    else:
        return wait.until(EC.presence_of_element_located((p_by, p_selector)))


def login_to_coupang(driver, username=None, password=None):
    """쿠팡 로그인 페이지에서 ID, PW 입력과 로그인 버튼 클릭은 사용자가 직접 합니다."""
    driver.get('https://www.coupang.com')
    
    # 로그인 버튼 클릭
    login_button = find_element(driver, "clickable", By.LINK_TEXT, "로그인")
    login_button.click()

    print(f"로그인 페이지가 열렸습니다. {LOGIN_TIMEOUT}초 내에 직접 로그인해주세요.")
    
    # 특정 element 로딩 감지 (예: 로그인 완료 후 나타나는 element)
    WebDriverWait(driver, LOGIN_TIMEOUT).until(
        EC.presence_of_element_located((By.ID, "headerMenu"))
    )
    
    # 로그인 성공 확인
    print("로그인 성공 감지. 스크래핑 재개...")
    

def go_to_order_list(driver):
    """주문 목록 페이지로 이동"""
    my_coupang_link = find_element(driver, "clickable", By.LINK_TEXT, "마이쿠팡")
    my_coupang_link.click()
    print("마이쿠팡 클릭...")


def scrape_order_data_into_df(driver, start_date=None, end_date=None):
    """
    쿠팡 주문 데이터를 스크래핑하여 pandas DataFrame에 저장

    - Args:
        driver: Selenium WebDriver
        start_date: 시작 날짜 (str, "YYYY.MM.DD" 형식, 예: "2024.06.01")
        end_date: 종료 날짜 (str, "YYYY.MM.DD" 형식, 예: "2024.08.01")

    - Returns:
        DataFrame: 스크래핑된 주문 데이터
    """

    if start_date:
        start_date = datetime.datetime.strptime(start_date, "%Y.%m.%d")

    if end_date:
        end_date = datetime.datetime.strptime(end_date, "%Y.%m.%d")
        
    
    df_orders = pd.DataFrame(columns=['date', 'product', 'price', 'url', 'order_status', 'split_product', 'memo', 'category1', 'category2'])

    order_section_xpath = '//*[@id="__next"]/div[2]/div[2]/div'        
    
    cnt_while = 0
    cnt_page = 0
    
    bl_while = True
    
    while bl_while:
        # 페이지 로딩 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "sc-gnmni8-0"))  # 주문 목록 테이블 클래스
        )

        order_section = find_element(driver, "presence", By.XPATH, order_section_xpath)
        soup = BeautifulSoup(order_section.get_attribute('innerHTML'), 'html.parser')
        
        # 각 주문 날짜 블록을 찾습니다.
        order_date_blocks = soup.select(".sc-fimazj-0.gKYVxm")       
         
        for order_date_block in order_date_blocks:
            # 주문 날짜 블록에서 주문 날짜를 찾습니다. 
            order_date_element = order_date_block.select_one(".sc-abukv2-1.kSZYgn")

            date_parts = [
                int(part) for part in order_date_element.get_text(strip=True).replace(". ", " ").split() if part.isdigit()
            ]


            order_date = datetime.datetime(date_parts[0], date_parts[1], date_parts[2])
                        
            
            # 날짜 필터링
            # my_data.get(["2024.08.30", ])  # 2024.08.30 부터 현재까지 주문 목록 조회
            if (start_date and order_date < start_date) and (end_date is None):
                print(f"if ({start_date} < {order_date}) and ({end_date} is None) break1...")
                bl_while = False
                break
            
            # my_data.get("2024.08.13")  # 2024.08.13 일자의 주문 목록 조회
            # my_data.get(["2024.09.02", "2024.10.04"])  # 특정 기간의 주문 목록 조회    
            if (start_date and order_date < start_date) and (end_date is not None):
                print(f"if ({order_date} < {start_date}) and ({end_date} is not None) break2...")
                bl_while = False # start_date보다 과거면 전체 루프 종료
                break
            
            # my_data.get("2024.08.13")  # 2024.08.13 일자의 주문 목록 조회
            # my_data.get([None, "2024.07.06"])  # 처음부터 2024.08.12 까지 주문 목록 조회
            if end_date and order_date > end_date:
                print(f"if {order_date} > {end_date} continue...")
                continue  
            

            date_text = f"{date_parts[0]:04d}.{date_parts[1]:02d}.{date_parts[2]:02d}"

            # 주문 날짜 블록에서 모든 배송 묶음을 찾습니다.
            order_bundle_sections = order_date_block.select(".sc-gnmni8-0.elGTUw")

            for order_bundle in order_bundle_sections:                
                # 배송 상태 추출
                target_div = order_bundle.select_one("div.sc-ki5ja7-1.krPkOP")
                order_status = target_div.contents[0].get_text(strip=True) if target_div else None
                
                product_rows = order_bundle.select(".sc-gnmni8-3.gmGnuU")  # 주문 상품 정보가 있는 행          
                                
                for row in product_rows:                
                    # 각 묶음에서 상품 정보를 담고 있는 엘리먼트들을 찾습니다. 
                    product_info_list = row.select(".sc-9cwg9-1.gLgexz")

                    for product_info in product_info_list:
                        product_name = product_info.select_one(".sc-8q24ha-1.ifMZxv").get_text(strip=True)  # 상품명
                        product_price = product_info.select_one(".sc-8q24ha-3.gFbjJh > .sc-uaa4l4-0 > span:nth-child(1)").get_text(strip=True) # 가격 

                        # 제품 상세 페이지 URL 추출
                        product_detail_url_part = product_info.select_one('a.hPjYZj')['href']
                        product_detail_url = f"https://mc.coupang.com{product_detail_url_part}"
                        
                        # 분리 배송 여부 확인
                        split_product_element = product_info.select_one(".sc-4dgk5r-0.dDFKxb > span.sc-755zt3-0.hullgd")
                        split_product = split_product_element.get_text(strip=True) if split_product_element else ""

                        # 배송 묶음에서 추출한 date_text를 사용하여 df_orders 데이터프레임에 추가
                        df_orders.loc[len(df_orders)] = [
                            date_text, 
                            product_name, 
                            product_price, 
                            product_detail_url, 
                            order_status, 
                            split_product, 
                            "", 
                            "", 
                            ""
                        ]

            print(f"{cnt_while} 번째 주문물품 스크래핑 완료...")
            cnt_while += 1        
        
        # 다음 페이지 버튼
        try:
            next_button = find_element(driver, "clickable", By.CSS_SELECTOR, ".sc-1o307be-0.jOhOoP > button:nth-child(2)")       

            next_button.click()
            
            time.sleep(2)  # 페이지 로딩 대기
            
            print(f"{cnt_page} 번째 주문목록 페이지 스크래핑 완료...")
            cnt_page += 1
            
        except TimeoutException:
            print(f"마지막 {cnt_page-1} 페이지입니다.")
            break
        

    # 배송 상태가 '취소 완료'인 주문 물품 가격을 'memo' 컬럼에 'price : 가격' 메모하고, 'price' 컬럼의 값을 0 으로 변경합니다.
    for i in df_orders.index:
        if df_orders.loc[i, 'order_status'] == '취소완료':
            df_orders.loc[i, 'memo'] = 'price : ' + df_orders.loc[i, 'price']
            df_orders.loc[i, 'price'] = '0 원'
            
    
    # df_orders 의 url 컬럼 값을 beautifulsoup 으로 접속해서 물품상세 페이지의 상단에 있는 상품 분류 카테고리 항목의 아이템 중에서
    # 항상 마지막 2 개 항목 값을 추출해서 df_orders 의 새로운 컬럼 'category1', 'category2' 컬럼 값으로 저장합니다.    
    for i in df_orders.index:
        product_page_url = df_orders.loc[i, 'url']
        driver.get(product_page_url)
        time.sleep(2)
        soup_product = BeautifulSoup(driver.page_source, 'html.parser')
        categories = soup_product.select("#breadcrumb > li > a.breadcrumb-link")
        if len(categories) >= 2:
            df_orders.loc[i, 'category1'] = categories[-2].text.strip()
            df_orders.loc[i, 'category2'] = categories[-1].text.strip()        
    
    return df_orders


def save_to_csv(df_orders):
    """주문 데이터를 CSV 파일로 저장"""
    df_orders_csv = df_orders.copy()
    
    # 'date', 'price', 'url' 컬럼 값이 같고 'split_product' 컬럼 값이 '분리 배송'인 행을 찾습니다.
    duplicated_rows = df_orders_csv[
        df_orders_csv.duplicated(subset=['date', 'price', 'url'], keep=False) & (df_orders_csv['split_product'] == '분리 배송')
    ]
    
    # 중복된 행 중 첫 번째 행을 제외하고 모두 삭제합니다.
    df_orders_csv = df_orders_csv.drop(duplicated_rows.index[1:])

    datelast = df_orders_csv['date'].iloc[0]
    datefirst = df_orders_csv['date'].iloc[-1]  

    # 현재 날짜와 시간을 가져와서 파일 이름에 추가
    now = datetime.datetime.now()
    yyyymmdd = now.strftime("%Y%m%d")
    hhmm = now.strftime("%HH%M")
        
    filename = f'coupang_orders_from{datefirst}_to{datelast}_at{yyyymmdd}-{hhmm}.csv'        
    
    df_orders_csv.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"주문 데이터가 {filename} 파일로 저장되었습니다...")


# --- 메인 실행 부분 ---
def get(date_range=None):
    """
    - 쿠팡 '주문목록' 데이터를 추출    
    
    - 호출 예시:
        # my_data.get()  # 전체 주문 목록 조회          
        # my_data.get("2024.08.13")  # 2024.08.13 일자의 주문 목록 조회
        # my_data.get(["2024.08.30", ])  # 2024.08.30 부터 현재까지 주문 목록 조회
        # my_data.get([None, "2024.07.06"])  # 처음부터 2024.07.06 까지 주문 목록 조회        
        # my_data.get(["2024.09.02", "2024.10.04"])  # 특정 기간의 주문 목록 조회    
    """
    
    # 날짜 범위 초기화
    start_date = None
    end_date = None

    # 인자에 따라 날짜 처리
    if date_range is None:
        # 1. 인자가 없을 때: 전체 주문 목록 조회 (start_date와 end_date가 None)
        pass
    elif isinstance(date_range, str):
        # 2. 인자가 문자열일 때: 특정 일자의 주문 목록 조회
        start_date = date_range
        end_date = date_range  # start_date와 end_date가 동일
    elif isinstance(date_range, list):
        # 3. 인자가 리스트일 때
        # print(len(["2024.06.01", ])) # 1
        # print(len([None, "2024.06.01"])) # 2
        if len(date_range) > 0:
            start_date = date_range[0]  # 리스트 첫 번째 요소를 start_date로 사용 (3, 4, 5 처리)
        if len(date_range) > 1:
            end_date = date_range[1]  # 리스트 두 번째 요소를 end_date로 사용 (4, 5 처리)

    driver = setup_driver()
    
    try:
        # 로그인 및 주문 목록 페이지로 이동
        login_to_coupang(driver)
        go_to_order_list(driver)

        # scrape_order_data_into_df()에 start_date와 end_date 전달
        orders = scrape_order_data_into_df(driver, start_date=start_date, end_date=end_date)

        # 주문 내역을 CSV 파일로 저장
        save_to_csv(orders)

        print("주문 목록이 성공적으로 스크래핑되고 저장되었습니다.")
        # input("Press Enter to quit...")
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
    finally:
        driver.quit()



if __name__ == "__main__":
    # CLI로 전달된 인자 처리 (명령행에서 입력된 인자)
    start_date = None
    end_date = None

    # 인자가 전달되면, 순서대로 start_date, end_date에 할당
    if len(sys.argv) > 1:
        start_date = sys.argv[1] if sys.argv[1] != "None" else None

    if len(sys.argv) > 2:
        end_date = sys.argv[2] if sys.argv[2] != "None" else None

    # get(start_date=start_date, end_date=end_date)    
    get()    
    
