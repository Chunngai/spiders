#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import os
import time
import re
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options


def generate_url(word_):
    print("Generating url...")
    searching_url_ = "https://image.baidu.com/search/index?tn=baiduimage&word={}".format(word_)
    print('Done')
    return searching_url_


def load_img(searching_url_):
    print("Loading images...")
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(options=chrome_options)

    driver.get(searching_url_)
    time.sleep(3)

    for i in range(1):
        ActionChains(driver).send_keys(Keys.END).perform()
        time.sleep(1)

    html_text_ = driver.page_source
    print('Done')
    return html_text_


def get_img_url_ext(html_text_):
    print('Retrieving image urls...')
    soup = BeautifulSoup(html_text_, 'html.parser')
    div_imgid_ = soup.find('div', id='imgid')

    li_s_ = div_imgid_.find_all('li')
    img_url_ext_ = {}
    for li_ in li_s_:
        try:
            img_url_ext_.update({li_['data-objurl']: li_['data-ext']})
        except KeyError:
            pass

    print("Done")
    print("{} img urls got".format(len(img_url_ext_)))
    return img_url_ext_


def process_file_name(url, ext):
    print('Processing img name...')

    try:
        img_name_ = url[-15:-6]
        pat = re.compile(r'[\\/:*?"<>|]')
        img_name_ = pat.sub('_', img_name_)

        print('Done')
        return img_name_
    except AttributeError:
        print('Failed to save img from {}!'.format(url))
        return ''


def download_imgs(download_urls_1_, word_):
    print('Saving imgs...')
    print('Making new dir {}...'.format(word_))
    try:
        os.mkdir(word_)
    except FileExistsError:
        print('Directory {} already exists!'.format(word_))
        pass
    else:
        print('Done\n')

    count = 0
    for url, ext in download_urls_1_.items():
        print('saving img from {}...'.format(url))
        try:
            r = requests.get(url, timeout=0.3)
            r.raise_for_status()
        except:
            print('Failed to retrieve img!\n')
            continue
        else:
            img_name_ = process_file_name(url, ext)
            if img_name_:
                path_ = os.path.join(os.getcwd(), word_, img_name_)
                with open(path_ + '.' + ext, 'wb') as f:
                    f.write(r.content)
                    count += 1
                print('img saved!\n')
    print('{} imgs saved!'.format(count))


if __name__ == "__main__":
    word = input("Input a key word of images to be found >>> ")
    searching_url = generate_url(word)
    html_text = load_img(searching_url)

    img_url_ext = get_img_url_ext(html_text)
    download_imgs(img_url_ext, word)
