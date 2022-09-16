# coding: utf8
# title: Add Booktoki.com
# author: github.com/STR-HK/hdl-stubs
# comment: Created at 12022/09/17

from fileinput import filename
from io import BytesIO
import re
import requests
from utils import Soup, LazyUrl, Downloader, Session, clean_title
import clf2
import json


class Image(object):
    def __init__(self, src, name):
        ext = ".{}".format(src.split(".")[-1])
        if ext.lower()[1:] not in ["jpg", "jpeg", "bmp", "png", "gif", "webm", "webp"]:
            ext = ".jpg"
        self.filename = f"{name}{ext}"
        self.url = LazyUrl(src, lambda _: src, self)


@Downloader.register
class Downloader_Booktoki(Downloader):
    type = "booktoki"
    URLS = [r"regex:booktoki[0-9]*\.com"]
    MAX_CORE = 4
    icon = "https://booktoki153.com/img/book/favicon-32x32.png"

    def read(self):
        soup = get_soup(self.url)

        artist = get_artist(soup)
        title = f"[{artist}] {get_title(soup)}"
        self.artist = artist

        src = soup.find("div", class_="view-img").find("img")["src"]
        img = Image(src, "cover")
        self.urls.append(img.url)

        pages = get_pages_list(soup)
        self.print_(pages)
        for n, page in enumerate(pages):
            self.title = f"{title} ({n+1}/{len(pages)})"
            self.print_(f"Reading: {n+1}/{len(pages)}")
            pagesoup = get_soup(page)

            @try_n(4)
            def ctt_foo():
                try:
                    return get_content(pagesoup)
                except:
                    return get_content(get_soup(page))

            content = ctt_foo()

            f = BytesIO()
            f.write(content.replace("&nbsp;", "\n").encode("UTF-8"))
            f.seek(0)

            @try_n(4)
            def fne_foo():
                try:
                    return f"{get_page_title(pagesoup)}.txt"
                except:
                    return f"{get_page_title(get_soup(page))}.txt"

            self.filenames[f] = fne_foo()
            self.urls.append(f)

        self.title = title


def get_soup(url):
    html = clf2.solve(url)["html"]
    return Soup(html)


def get_pages_list(soup):
    pages_list = []
    list_body = soup.find("ul", class_="list-body")
    list_items = list_body.find_all("li", class_="list-item")
    for list_item in list_items:
        page = list_item.find("a")["href"]
        pages_list.append(page)
    pages_list.reverse()
    return pages_list


def get_info_list(soup):
    """
    -> [
        title,
        [
            platform,
            tags,
            artist
        ],
        summary
    ]
    """
    infobox = soup.find("div", class_="col-sm-8")
    contents = infobox.find_all("div", class_="view-content")
    details = contents[1].get_text().split("\xa0")
    for n, detail in enumerate(details):
        details[n] = detail.strip()
    return [contents[0].get_text().strip(), details, contents[2].get_text().strip()]


def get_content(soup):
    novel = soup.find("div", {"id": "novel_content"})
    ps = novel.find_all("p")
    if len(novel.find_all("p")) != 0:
        text = ""
        for n, p in enumerate(ps):
            if p.get_text() != "":
                text += p.get_text()
            else:
                text += "\n"
            text += "\n"
    else:
        text = novel.get_text()
    return text


def get_title(soup):
    return get_info_list(soup)[0]


def get_artist(soup):
    return get_info_list(soup)[1][2]


def get_page_title(soup):
    full = soup.find("div", class_="toon-title")
    span = full.find("span").get_text()
    title = full.get_text().replace(span, "").strip()
    return clean_title(title)


log(f"Site Added: Booktoki")
