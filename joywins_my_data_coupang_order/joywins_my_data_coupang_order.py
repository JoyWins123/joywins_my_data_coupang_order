""" 
# coupang-order-scraper

## 쿠팡 주문 목록 스크래퍼

### 라이선스

MIT License

### 개요

- Selenim 으로 쿠팡 접속해서 마이쿠팡에서 '주문목록' 데이터 추출하고 CSV 파일로 저장하는 모듈입니다. 


### 기능

- 사용자 로그인 후 주문 목록 페이지에 접근
- 주문 날짜, 상품명, 가격, URL, 주문 상태, 분리 배송 여부 등의 정보 스크래핑
- 스크래핑된 데이터를 Pandas DataFrame에 저장 후 CSV 파일로 저장

### 설치

> pip install coupang-order-scraper


### 사용법

1. 터미널에서 `coupang-order-scraper` 명령을 실행합니다.
2. Selenium이 실행되어 크롬 웹브라우저가 열리고 쿠팡 로그인 페이지로 이동합니다.
3. 30초 내에 쿠팡 웹사이트에 직접 로그인합니다.
4. 로그인이 완료되면 자동으로 주문 목록 스크래핑이 시작됩니다.
5. 스크래핑이 완료되면 CSV 파일로 저장됩니다.


### 주의 사항

- 쿠팡 웹사이트의 구조 변경에 따라 스크래핑 코드가 작동하지 않을 수 있습니다.
- 쿠팡 이용 약관을 준수하여 사용해야 합니다.
"""


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
    """랜덤한 데스크탑 User-Agent를 반환합니다."""
    ua = UserAgent()
    while True:
        user_agent = ua.random
        if "Mobi" not in user_agent and "Android" not in user_agent:
            return user_agent


def setup_driver():
    """Selenium WebDriver를 설정합니다."""
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
    """요소를 찾아 반환합니다."""
    if p_ec == "clickable":
        return WebDriverWait(p_driver, timeout).until(EC.element_to_be_clickable((p_by, p_selector)))
    elif p_ec == "visibility":
        return WebDriverWait(p_driver, timeout).until(EC.visibility_of_element_located((p_by, p_selector)))
    else:
        return WebDriverWait(p_driver, timeout).until(EC.presence_of_element_located((p_by, p_selector)))


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
    """주문 목록 페이지로 이동합니다."""
    my_coupang_link = find_element(driver, "clickable", By.LINK_TEXT, "마이쿠팡")
    my_coupang_link.click()
    print("마이쿠팡 클릭...")


def scrape_order_data_into_df(driver):
    """주문 데이터를 스크래핑하여 pandas DataFrame에 저장합니다."""
    
    df_orders = pd.DataFrame(columns=['date', 'product', 'price', 'url', 'order_status', 'split_product', 'memo', 'category1', 'category2'])

    order_section_xpath = '//*[@id="__next"]/div[2]/div[2]/div'        
    
    cnt_while = 0
    cnt_page = 0
    
    while True:
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
        
        # 다음 페이지 버튼 (Selenium WebDriver 객체로 찾기)
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
    """주문 데이터를 CSV 파일로 저장합니다."""
    df_orders_csv = df_orders.copy()
    
    # 'date', 'price', 'url' 컬럼 값이 같고 'split_product' 컬럼 값이 '분리 배송'인 행을 찾습니다.
    duplicated_rows = df_orders_csv[
        df_orders_csv.duplicated(subset=['date', 'price', 'url'], keep=False) & (df_orders_csv['split_product'] == '분리 배송')
    ]
    
    # 중복된 행 중 첫 번째 행을 제외하고 모두 삭제합니다.
    df_orders_csv = df_orders_csv.drop(duplicated_rows.index[1:])

    datefirst = df_orders_csv['date'].iloc[0]
    datelast = df_orders_csv['date'].iloc[-1]  

    # 현재 날짜와 시간을 가져와서 파일 이름에 추가
    now = datetime.datetime.now()
    yyyymmdd = now.strftime("%Y%m%d")
    hhmm = now.strftime("%HH%M")
        
    filename = f'coupang_orders_from{datefirst}_to{datelast}_at{yyyymmdd}-{hhmm}.csv'        
    
    df_orders_csv.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"주문 데이터가 {filename} 파일로 저장되었습니다...")


# --- 메인 실행 부분 ---
def main():    
    driver = setup_driver()
    
    try:
        login_to_coupang(driver)
        go_to_order_list(driver)
        orders = scrape_order_data_into_df(driver)
        save_to_csv(orders)
        
        input("Press Enter to quit...")
    except Exception as e:
        print(f"오류 발생: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
    
    
