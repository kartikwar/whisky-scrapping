# -*- coding: utf-8 -*-
"""
Kartik Sirwani
"""

from numpy import product
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from bs4 import BeautifulSoup as bs
import time
import pandas as pd
import re
import os


driver = webdriver.Chrome(executable_path='/usr/lib/chromium-browser/chromedriver')


def get_prod_info(prod_url):
    # prod_url = 'https://www.whiskyhammer.com/item/87702/Midleton/Redbreast---21-Year-Old.html'
    prod_info = {}
    driver.get(prod_url)
    time.sleep(1)
    try:
        prod_info['title'] = driver.find_element_by_css_selector(".lotNo h1").text
    except Exception as ex:
        prod_info['title'] = ''
    try:
        prod_info['lot_no'] = driver.find_element_by_css_selector(".lotNo span").text
    except Exception as ex:
        prod_info['lot_no'] = ''

    try:
        sold_eles = driver.find_elements_by_css_selector(".priceDesc")
        prod_info['sold_date'] = [ele.text for ele in sold_eles if 'SOLD' in ele.text ][0]
    except Exception as ex:
        prod_info['sold_date'] = ''

    try:
        prod_info['price'] = driver.find_element_by_css_selector(".GBP.show").text
    except Exception as ex:
        prod_info['price'] = ''

    # try:
    #     other_info = driver.find_elements_by_css_selector(".properties")[0].text.replace('Lot Information\n', '')
    #     other_info_attrs = other_info.split('\n')
    # except Exception as ex:
    #     other_info_attrs = []


    # for info_attr in other_info_attrs:
    #     try:
    #         info_attr = info_attr.split(':')
    #         prod_info[info_attr[0]] = info_attr[1].strip()
    #     except Exception as ex:
    #         prod_info[info_attr[0]] = ''
    
    try:
        prod_info['about'] = driver.find_element_by_css_selector(".wysiwyg").text
    except Exception as ex:
        prod_info['about'] = ''

    try:
        prod_info['awards'] = driver.find_elements_by_css_selector(".awardsList")[0].text
    except Exception as ex:
        prod_info['awards'] = ''

    try:
        elements = driver.find_elements_by_css_selector('.productDescription__item')
        for ele in elements:
            if 'Other Information' in ele.text:
                prod_info['other_info'] = ele.text
                break
    except Exception as ex:
        prod_info['other_info'] = ''

    try:
        prod_info['has_vat'] = False
        vat = driver.find_element_by_css_selector(".toolTip.tooltipLeft img").get_attribute('src')
        if vat is not None and vat != '':
            prod_info['has_vat'] = True
        # temp = 0
    except Exception as ex:
        temp = 0

    return prod_info
    


def get_product_links(url):
    products_links = []
    driver.get(url)
    products =  driver.find_elements_by_css_selector(".buttonAlt")
    products_links = [product.get_attribute('href') for product in products]
    return products_links

def process_master_url(url):
    process_status = True
    product_links = []
    infos = []

    url = url + '/?ps=500'

    while process_status:
        driver.get(url)
        time.sleep(5)
        try:
            cookie_button = driver.find_element_by_id('ccc-notify-accept')
            cookie_button.click()
            time.sleep(5)
            temp = 0
        except NoSuchElementException:
            print('no accept cookie button found')
        
        try:
            products =  driver.find_elements_by_css_selector(".itemImageWrap")
        except Exception as ex:
            products_links = []
            print('products not found')
        
        for product in products:
            try:
                product_link = product.find_element_by_tag_name('a').get_attribute('href')
                product_links.append(product_link)
                temp= 0
                # products_links = [product.get_attribute('href') for product in products]
            except Exception as ex:
                temp = 0

        try:
            next_li_element = driver.find_element_by_css_selector('li.next')
            next_url = next_li_element.find_element_by_tag_name('a').get_attribute('href')
            url = next_url
        except Exception as ex:
            next_url = None
            process_status = False

    #process product links now
    # for product_link in product_links:
    #     prod_info = get_prod_info(product_link)
    #     infos.append(prod_info)
    
    return product_links 

def get_auction_urls(auction_path):
    df = pd.read_csv(auction_path)
    all_urls = []
    for ind, row in df.iterrows():
        if row['Status'] != 1:
            # df.at[ind, 'Status'] = -1
            master_url = row['Page']
            row_links = process_master_url(master_url)
            all_urls += row_links
            # master_info.to_csv(dest_path, mode='a', header=False, index=False)
            # df.at[ind, 'Status'] = 1
            # print(type(row['Status']))
    # urls = list(['URL'])
    return all_urls

def initialize_columns(auction_df):
    first_row = auction_df.iloc[0]
    prod_url = first_row['url']
    prod_info = get_prod_info(prod_url)
    for key in prod_info.keys():
        auction_df[key] = ''
    # temp = 0
    return auction_df

def fill_df(df, ind, prod_info):
    for key, val  in prod_info.items():
        try:
            df.at[ind, key] = val
        except Exception as ex:
            print(ex)
    return df

if __name__ == "__main__":
    products = []

    auction_path = 'links.csv'
    dest_path = 'all_links.csv'

    if not os.path.exists(dest_path):
        auction_urls = get_auction_urls(auction_path)
        status = pd.Series([0 for i in range(len(auction_urls))], name='status')
        auction_urls = pd.Series(auction_urls, name='url')
        auction_df = pd.DataFrame({'url': auction_urls, 'status': status })
        auction_df.to_csv(dest_path, index=False)
    
    auction_df = pd.read_csv(dest_path)

    log_counter = 0

    initialize_columns(auction_df)

    for ind, row in auction_df.iterrows():
        try:
            status = auction_df['status']
            if status == 1:
                #skip the ones that were processed previously
                continue
            prod_url = row['url']
            prod_info = get_prod_info(prod_url)
            auction_df = fill_df(auction_df, ind, prod_info)
            auction_df.at[ind, 'status'] = 1
            if log_counter % 10 == 0:
                auction_df.to_csv(dest_path, index=False )
        except Exception as ex:
            print(ex)

    auction_df.to_csv(dest_path, index=False )    



