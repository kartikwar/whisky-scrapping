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


driver = webdriver.Chrome(executable_path='/usr/lib/chromium-browser/chromedriver')


def get_prod_info(prod_url):
    # prod_url = 'https://www.whiskyhammer.com/item/87702/Midleton/Redbreast---21-Year-Old.html'
    prod_info = {}
    driver.get(prod_url)
    time.sleep(1)
    try:
        prod_info['title'] = driver.find_element_by_css_selector(".innerText").text.split('\n')[0]
    except Exception as ex:
        prod_info['title'] = ''
    try:
        prod_info['lot_no'] = driver.find_element_by_css_selector(".lotNo").text
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

    try:
        other_info = driver.find_elements_by_css_selector(".properties")[0].text.replace('Lot Information\n', '')
        other_info_attrs = other_info.split('\n')
    except Exception as ex:
        other_info_attrs = []


    for info_attr in other_info_attrs:
        try:
            info_attr = info_attr.split(':')
            prod_info[info_attr[0]] = info_attr[1].strip()
        except Exception as ex:
            prod_info[info_attr[0]] = ''
    
    try:
        prod_info['about'] = driver.find_element_by_css_selector(".wysiwyg").text
    except Exception as ex:
        prod_info['about'] = ''

    try:
        prod_info['awards'] = driver.find_elements_by_css_selector(".awardsList")[0].text
    except Exception as ex:
        prod_info['awards'] = ''

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


def get_auction_urls(auction_path):
    urls = list(pd.read_csv(auction_path)['URL'])
    return urls


if __name__ == "__main__":
    products = []

    auction_path = '/home/kartik/Documents/personal_git/scrapping-whisky/auction_links.csv'


    auction_urls = get_auction_urls(auction_path)

    for auc_url in auction_urls:

    # auction_url = 'https://www.whiskyhammer.com/auction/past/auc-68/?ps=500'

        #get the url links of all the products on the website
        #in this the count would be 500
        products_links = get_product_links(auc_url)

        #for each product get product attributes one by one
        for prod_link in products_links:
            #get product info here
            try:
                prod_info = get_prod_info(prod_link)
                products.append(prod_info)
            except Exception as ex:
                print('ex')

    #save the final csv containing all info
    pd.DataFrame(products).to_csv('whisky_products.csv', index=False)



