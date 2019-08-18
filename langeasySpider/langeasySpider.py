#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re
import os

import requests
from bs4 import BeautifulSoup
from docx import Document


def make_request(url_, t_):

    # t_ == 't': return html text
    # t_ == 'b': return binary content
    try:
        r = requests.get(url_)
        r.raise_for_status()
    except:
        return "" if t_ == 't' else b''
    else:
        if t_ == 't':
            r.encoding = r.apparent_encoding
            return r.text
        else:
            return r.content


def get_ids(html_text_):
    courlist = json.loads(html_text_).get("courlist")
    id_list = [song.get("id") for song in courlist]

    return id_list


def make_soup(url_):
    html_text = make_request(url_, 't')
    soup = BeautifulSoup(html_text, "html.parser")

    return soup


def get_title_list(song_url_list_):
    title_list = []

    for url in song_url_list_:
        soup = make_soup(url)

        # find the title
        h5 = soup("h5", id="playerTitle")[0]
        title = h5.string

        title_list.append(title)

    return title_list


def get_raw_text_list(song_url_list_):
    raw_text_list = []

    for url in song_url_list_:
        soup = make_soup(url)

        try:
            # find the ul tag containing the text
            lrc_content = soup("ul", id="lrcContent")[0]

            # collect all paras in a list
            paras = []
            for tag in lrc_content:
                try:  # the tag identifier here may be a string like '\n'
                    if len(tag.string) and tag.string != '\n':
                        paras.append(tag.string)
                except:
                    continue
            raw_text_list.append(paras)
        except:
            raw_text_list.append([])

    return raw_text_list


def get_text_list(song_url_list_):
    raw_text_list = get_raw_text_list(song_url_list_)

    f_text_list_ = []
    zh_text_list_ = []
    bi_text_list_ = []

    for raw_text in raw_text_list:
        f_text = []
        zh_text = []
        bi_text = []
        # paras with Japanese chrs and less than 6 successive Chinese chrs
        # or paras with 6 successive Chinese chrs and followed with zero or one 」 than Japanese chrs
        # will be classified as Japanese paras
        # otherwise paras will be classified as Chinese paras
        pat1 = re.compile(u'[\u3040-\u30FF]')
        pat2 = re.compile(u'[\u4E00-\u9FA5]{6}')
        pat3 = re.compile(u'[\u4E00-\u9FA5]{6}」?[\u3040-\u30FF]')
        for string in raw_text:
            rst1 = pat1.search(string)
            rst2 = pat2.search(string)
            rst3 = pat3.search(string)

            if (rst1 and not rst2) or rst3:
                f_text.append(string)
            else:
                zh_text.append(string)

        # if the text contains both foreign language paras and Chinese paras, it is bilingual
        if len(f_text) != 0 and len(zh_text) != 0:
            bi_text = raw_text

        f_text_list_.append(f_text)
        zh_text_list_.append(zh_text)
        bi_text_list_.append(bi_text)

    # print(len(f_text_), len(zh_text_), len(bi_text_))
    return f_text_list_, zh_text_list_, bi_text_list_


def get_audio_list(song_url_list_):
    audio_list = []

    for url in song_url_list_:
        soup = make_soup(url)

        # find the download url of the audio
        audio_tag = soup("audio", id="audio")[0]
        audio_url = audio_tag["src"]

        # downloasd the audio
        audio = make_request(audio_url, 'b')

        audio_list.append(audio)

    return audio_list


def create_dir(title_):
    path = os.path.join(os.getcwd(), "每日一更NHK（听写版）", title_)
    try:
        os.makedirs(path)
        return path
    except:
        return ''


def save_data(f_text_list_, zh_text_list_, bi_text_list_, audio_list_, title_list_):
    for i in range(len(f_text_list_)):
        # create the directory for the title if the title does not exist
        path_0 = create_dir(title_list_[i])

        if path_0:
            data_list = [f_text_list_[i], zh_text_list_[i], bi_text_list_[i], audio_list_[i]]
            pre = ["f_", "zh_", "bi_", "a_"]
            ext = [".docx", ".docx", ".docx", ".mp3"]
            path_list = [os.path.join(path_0, pre[j] + title_list_[i] + ext[j]) for j in range(len(pre))]
            # save texts
            for k in range(3):
                document = Document()
                for para in data_list[k]:
                    document.add_paragraph(para+'\n')
                document.save(path_list[k])

            # save audio
                with open(path_list[3], "wb") as f:
                    f.write(data_list[3])


def langeasy_spider():
    page_num = 0
    while True:
        # generate the url of every page
        page_num += 1
        page_url = "https://www.langeasy.com.cn/getBookInfo.action?bookid=644573219&courpage={}&courrows=14&pubstate=2&\
        sorttype=0".format(page_num)

        r_text = make_request(page_url, 't')
        # if the condition is True, data of the last page has been saved in the previous loop
        # and urls from this loop are invalid
        if "song" not in r_text:
            break

        # get an id list
        id_list = get_ids(r_text)
        # generate song urls
        song_url_list = ["https://www.langeasy.com.cn/m/player?f={}&ct=web".format(id_) for id_ in id_list]

        # get names
        title_list = get_title_list(song_url_list)
        # get texts
        f_text_list, zh_text_list, bi_text_list = get_text_list(song_url_list)
        # get tue audio
        audio_list = get_audio_list(song_url_list)
        # save data
        save_data(f_text_list, zh_text_list, bi_text_list, audio_list, title_list)


if __name__ == '__main__':
    langeasy_spider()
