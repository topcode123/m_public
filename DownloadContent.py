
from newspaper import Config
from sys import prefix
from pymongo import MongoClient
import time
from concurrent.futures import ThreadPoolExecutor,ProcessPoolExecutor
import socket
import html.parser    
import urllib
import requests
from requests.models import HTTPBasicAuth
from Settings import *
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
from SpinService import *
import json
from unidecode import unidecode
from Tile import *
import random
import socket
import requests
import json
import base64
from newspaper import Article
import lxml
import html
import html.parser  
from concurrent.futures import ThreadPoolExecutor
from Settings import *
from bson import ObjectId

from pymongo import MongoClient
import time
from PIL import Image
import io
from unidecode import unidecode
#from bing_image_urls import bing_image_urls
#from underthesea import word_tokenize as word_tokenize_vi
from bingimages import *

class DownloadContent:

    def __init__(self) -> None:
        self.client = MongoClient(CONNECTION_STRING_MGA1)
        # self.executor = ThreadPoolExecutor() # Or ProcessPoolExecutor

        self.db = self.client.url
        #self.client.drop_database("url")
        self.db1 = self.client.content
        self.cl = self.client.queuekeywords.data
        self.spinService = SpinService()
        self.passurl =  self.client.passsurl
        self.blacklist= self.client.blacklist
    def replace_attr(self,soup, from_attr: str, to_attr: str) -> str:
        tags = soup(attrs={from_attr: True})
        for tag in tags:
            tag[to_attr] = tag[from_attr]
            del tag[from_attr]
        return soup
        
    def process_content(self,tag):
        if tag["language"] == "vi":
            tagstring = self.spinService.spin_paragraph(tag["ptag"],tag["keywords"])
        elif tag["language"] == "en":
            tagstring= self.spinService.spin_paragraph_en(tag["ptag"],tag["keywords"])
        return tagstring

    def download_html(self,url):
        # try:
            if self.client.passsurl[url["keyword"]["UserId"]].count_documents({"link":url["link"]})>0:
                #raise ValueError("link exist in existurl of {}".format(url["keyword"]["UserId"]))
                if url["keyword"]["start"]<10:
                    keyword = url["keyword"]
                    keyword["start"] = keyword["start"]+1
                    self.cl = self.client.queuekeywords.data.insert_one(keyword)
                    return keyword
                else:
                    return None
            domain = urlparse(url["link"]).netloc
            if self.client.blacklist[url["keyword"]["UserId"]].count_documents({"domain":domain})>0:
                #raise ValueError("link exist in blacklist of {}".format(url["keyword"]["UserId"]))
                if url["keyword"]["start"]<10:
                    keyword = url["keyword"]
                    keyword["start"] = keyword["start"]+1
                    self.cl = self.client.queuekeywords.data.insert_one(keyword)
                    return keyword
                else:
                    return None
            self.client.passsurl[url["keyword"]["UserId"]].insert_one({"link":url["link"]})


            config = Config()
            config.request_timeout = 10
            config.browser_user_agent = random.choice(USER_AGENT)
            article = Article(url["link"],keep_article_html=True,config=config)
            article.download()
            soup = BeautifulSoup(article.html, 'html.parser')
            soup =self.replace_attr(soup,'data-src', 'src')
            soup =self.replace_attr(soup,'data-lazy-src', 'src')
            soup =self.replace_attr(soup,'lazy-src', 'src')
            soup =self.replace_attr(soup,'data-srcset', 'srcset')
            soup =self.replace_attr(soup,'data-lazy-srcset', 'srcset')
            soup =self.replace_attr(soup,'lazy-srcset', 'srcsets')
            soup =self.replace_attr(soup,'data-original', 'src')
            article.html =str(soup)
            article.parse()
            if (len(article.text.split(" "))>400 and article.meta_lang==url["keyword"]["lang"]):
                print(url['keyword']['keyword'])

                soup = BeautifulSoup(article.article_html, 'html.parser')
                self_url = unidecode(url['keyword']['keyword'])+ ' ' + str(time.time()).split(".")[0]
                self_url = self_url.replace(" ","-")
                self_url = self_url.replace(".","")
                domain = urlparse(url["link"]).netloc
                img = soup.find_all("img")
                scr_img = []
                pre_link = None
                for i in img:
                    if pre_link!= None:
                        if i.has_attr("src") and pre_link.has_attr("src"):
                            if pre_link["src"] == i["src"]:
                                aa = soup.new_tag("br")
                                i.replace_with(aa)
                                pre_link = i
                                continue
                    pre_link = i
                    if i.has_attr("src"):
                        if i["src"][0:3] =="/up" or i["src"][0:4] =="/pic" or i["src"][0:6] =="/media":
                           i["src"] = "http://"+domain +i["src"]
                        scr_img.append(i["src"])
                    else:
                        aa= soup.new_tag("br")
                        i.replace_with(aa)
                    i['style'] ="width:100%"
                thumb = None
                if len(scr_img)>2:
                    h =len(scr_img)
                    thumb = scr_img[h-2]
                elif len(scr_img)==2:
                    h =len(scr_img)
                    thumb = scr_img[1]
                elif len(scr_img)==1:
                    h =len(scr_img)
                    thumb = scr_img[0]
                aaaaa =json.loads(requests.get("https://{}/wp-json/wp/v2/posts?categories={}".format(url['keyword']["urlbase"],url["keyword"]["category"])).text)
                if len(aaaaa)>0:
                    internal_link_total = random.choice(aaaaa)
                    internal_link = internal_link_total["link"]
                    internal_link_title = internal_link_total["title"]["rendered"]
                    internal_link_total2 = random.choice(aaaaa)
                    internal_link2 = internal_link_total2["link"]
                    internal_link_title2 = internal_link_total2["title"]["rendered"]
                cate_name = json.loads(requests.get("https://{}/wp-json/wp/v2/categories/{}".format(url['keyword']["urlbase"],url["keyword"]["category"])).text)["name"]
                cate_link = json.loads(requests.get("https://{}/wp-json/wp/v2/categories/{}".format(url['keyword']["urlbase"],url["keyword"]["category"])).text)["link"]

                # scr_img = scr_img.append(article.top_image) 
                #scr_img = bing_image_urls(url['keyword']['keyword'], limit=1)
                article.article_html = str(soup)
                paper = html.unescape(article.article_html)
                paper = BeautifulSoup(paper,"html.parser")
                for elem in paper.find_all(['a']):
                    elem.unwrap()
                domain = domain.split(".")
                domain[-2] = list(domain[-2])
                domain[-2][0] = ".?"
                domain[-2][-1] = ".?"
                domain[-2][2] = ".?"
                domain[-2][-2] = ".?"
                domain[-2] = "".join(domain[-2])
                domain = ".".join(domain)
                article.title = re.sub(re.compile(domain),url['keyword']["urlbase"],article.title)
                titles = []
                for i in article.title.split(" "):
                    if ".com" in i or ".org" in i or ".vn" in i or ".us" in i or ".net" in i :
                        titles.append(url['keyword']["urlbase"])
                    else:
                        titles.append(i)
                article.title = " ".join(titles)
                if article.meta_lang == "vi":
                    article.title = self.spinService.spin_title_vi(article.title,url['keyword']['keyword'])
                else:
                    article.title = self.spinService.spin_title_en(article.title,url['keyword']['keyword'])
                article.title = article.title.replace(" . ",".")
                for elem in paper.find_all(["img"],{"alt":re.compile(domain)}):
                    elem['alt'] =re.sub(re.compile(domain),url['keyword']["urlbase"],elem['alt'])
                for elem in paper.find_all(text = re.compile(domain)):
                    elem = elem.replace_with(re.sub(re.compile(domain),url['keyword']["urlbase"],elem))
                heading_p = []
                for heading in soup.find_all(["h1", "h2", "h3"]):
                    for p in heading.find_all("p"):
                        heading_p.append(p)
                thepp =  paper.find_all('p')
                thep = []
                for i in thepp:
                    if i not in heading_p:
                        thep.append(i)

                if len(aaaaa)>0:
                    internal_link_p_tag1 =  '<div style="margin-bottom:15px;margin-top:15px;"><p style="padding: 20px; background: #eaf0ff;">Xem thêm: <a target="_blank" href="{}" rel="bookmark" title="{}">{}</a> </p></div>'.format(internal_link,internal_link_title,internal_link_title)
                    self_link_p_tag =  '<div style="margin-bottom:15px;margin-top:15px;"><p style="padding: 20px; background: #eaf0ff;">Bạn đang đọc: <a target="_blank" href="{}" rel="bookmark" title="{}">{}</a> </p></div>'.format("http://"+url['keyword']["urlbase"]+'/'+self_url,article.title,article.title)
                    internal_link_p_tag2 =  '<div style="margin-bottom:15px;margin-top:15px;"><p style="padding: 20px; background: #eaf0ff;">Xem thêm: <a target="_blank" href="{}" rel="bookmark" title="{}">{}</a></p></div>'.format(internal_link2,internal_link_title2,internal_link_title2)

                    internal_link_p_tag1 = BeautifulSoup(internal_link_p_tag1,"html.parser")
                    self_link_p_tag = BeautifulSoup(self_link_p_tag,"html.parser")
                    internal_link_p_tag2 = BeautifulSoup(internal_link_p_tag2,"html.parser")
                    thep[3].append(self_link_p_tag)

                    thep[int(len(thep)/2)].append(internal_link_p_tag1)

                    thep[len(thep)-4].append(internal_link_p_tag2)

                nguon = '<div style="margin-bottom:15px;margin-top:15px;"><p style="padding: 20px; background: #eaf0ff;">Source: <a target="_blank" href="{}" rel="bookmark" title="{}">{}</a> <br> Category: <a target="_blank" href="{}" rel="bookmark" title="{}">{}</a> </p></div>'.format("http://"+url['keyword']["urlbase"]+'/',url['keyword']["urlbase"],url['keyword']["urlbase"],cate_link,cate_name,cate_name)

                nguon = BeautifulSoup(nguon,"html.parser")

                paper.append(nguon)
                listp = [{"ptag":m,"keywords":url["keyword"]["keyword"],"language":article.meta_lang} for m in paper.find_all("p")]
                resultp= []
                for i in listp:
                    if i["language"]== "vi":
                        resultp.append(self.spinService.spin_paragraph(i["ptag"],i["keywords"]))
                    else:
                        resultp.append(self.spinService.spin_paragraph_en(i["ptag"],i["keywords"]))


                for k1,k2 in zip(listp,resultp):
                    k1["ptag"].replace_with(k2)
                paper = str(paper)
                paper  = paper.replace("&lt;","<")
                paper  = paper.replace("&gt;",">")
                paper= paper.replace(" . ", ". ")
                paper = paper.replace(" , ", ", ")



                content = {
                    "user":url["user"],
                    "title":article.title,
                    "content":str(paper),
                    "category":url["keyword"]["category"],
                    "language":article.meta_lang,
                    "url_img":thumb,
                    "keywords":url["keyword"]["keyword"],
                    "slug":self_url
                }
                self.db1[content["UserId"]].insert_one(content)
                return content
            else:
                if url["keyword"]["start"]<10:
                    keyword = url["keyword"]
                    keyword["start"] = keyword["start"]+1
                    self.cl = self.client.queuekeywords.data.insert_one(keyword)
                    return keyword
                else:
                    return None
        # except:
        #     print(url['keyword']["urlbase"])

        #     if url["keyword"]["start"]<10:
        #         keyword = url["keyword"]
        #         keyword["start"] = keyword["start"]+1
        #         return keyword

    def MultiDownloadContent(self):
        listurl = []
        results = []
        with self.db.watch()  as stream:
            while stream.alive:
                listCollections = self.db.collection_names({})

                while len(listCollections)>0:
                    for i in listCollections:
                        if self.db[i].count_documents({})>0:
                            a = self.db[i].find_one_and_delete({})
                            if a!=None:
                                self.download_html(a)
                        else:
                            self.db[i].drop()
                        listCollections = self.db.collection_names({})

DownloadContent().MultiDownloadContent()


