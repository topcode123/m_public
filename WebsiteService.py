from datetime import datetime, time, timedelta
from typing import Optional
import fastapi
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from starlette.status import HTTP_404_NOT_FOUND
from Settings import *
from pymongo import MongoClient
from bson import ObjectId
from urllib.parse import urlparse
from typing import Optional
import requests
import math
import aiohttp
import asyncio
from aiohttp import client
import async_timeout
import os
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
from requests.sessions import Session, session
from Settings import *
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
import json
from unidecode import unidecode
from aiohttp import request
from itertools import product
import requests
import json
import base64
import lxml
import html
import html.parser  
from Settings import *
from bson import ObjectId
from pymongo import MongoClient
import time
from PIL import Image
import io
from unidecode import unidecode
from aiohttp import request
from itertools import product
import aiofiles
from lxml.html import tostring
import traceback
class Website(BaseModel):
    Email:str
    Phone:str
    Website:str
    UserWP: str
    PasswordWP: str
    Blacklist:Optional[list]=[]
    Type: Optional[str]='Basic'
    Phone_replace: Optional[str]=''
    Email_replace: Optional[str]=''
    Text_replace:Optional[list]=[]
class WebsiteService:
    """
    database in mongodb: website
    - name
    - phone
    - email
    - website
    - userwp
    - passwordwp
    - type 
    """
    def __init__(self) -> None:
        self.website  = MongoClient(CONNECTION_STRING_MGA1).websites.websiteconfig
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        

    #Thêm mới website
    async def restImgUL(self,website,user,password,urlimg,request):
        newID = None
        if urlimg ==None or "base64" in urlimg:   
            async with aiofiles.open("articlewriting1.jpg", mode='rb') as f:
                image = await f.read()
                image = Image.open(io.BytesIO(image))
                path_files = "articlewriting1.jpg"
                output = io.BytesIO()
                image.save(output,format='JPEG',optimize = True,quality = 30)
                image = output.getvalue()
        else:
            try:
                path_files = urlimg.split("/")[-1]
                # r = await request.get(urlimg)
                async with request.get(urlimg) as response:
                    r = await response.read()
                image = Image.open(io.BytesIO(r))
                image = image.resize((900,603))
                output = io.BytesIO()
                if "JPG" in path_files.upper():
                    image.save(output,format='JPEG',optimize = True,quality = 30)
                elif "PNG" in path_files.upper():
                    image.save(output,format='PNG',optimize = True,quality = 30)
                image = output.getvalue()
            except Exception as e:
                print(website + ":" +str(e))
                async with aiofiles.open("articlewriting1.jpg", mode='rb') as f:
                    image = await f.read()
                    image = Image.open(io.BytesIO(image))
                    path_files = "articlewriting1.jpg"
                    output = io.BytesIO()
                    image.save(output,format='JPEG',optimize = True,quality = 30)
                    image = output.getvalue()
        with async_timeout.timeout(200):
            async with request.post(website,
                            data=image,
                            headers={ 'Content-Type': 'image/jpg','Content-Disposition' : 'attachment; filename=%s'%path_files},
                            auth=aiohttp.BasicAuth(user, password),ssl=False) as response:
                res1 = await response.text(encoding="utf-8")

                res = await response.json(encoding="utf-8")
                # print(res1)
                # print(res)
                newID= res.get('id')
        return newID
    async def AddWebsite(self,UserId:str,Email:str,Phone:str,website:str,UserWP:str,PasswordWP:str,Blacklist,Phone_replace,Email_replace,Text_replace,Type:Optional[str]='Basic'):
        '''
        Token: Tài khoản sau khi login sẽ tạo ra một token để dùng xác thực cho các api sau này.
        UserWP: Là thông tin username đăng nhập vào hệ thống wp-admin.
        Password WP: là thông tin về mật khẩu của ứng dụng.
        Response:+ Nếu chưa đăng nhập hoặc token hết hạn sẽ báo lỗi 401 unauthorized
                + Nếu xác thực thông tin đăng nhập thành công thì sẽ cho tạo website và lúc này Active = False đợi admin xác thực.
                + Process là id chiến dịch mà hệ website đang chạy
        '''
        imageid = None
        session_timeout =   aiohttp.ClientTimeout(total=None,sock_connect=1000,sock_read=1000)
        try:
            async with aiohttp.ClientSession(trust_env=True,timeout=session_timeout) as session:
                imageid = await self.restImgUL(website+"/wp-json/wp/v2/media",UserWP,PasswordWP,None,session)
        except Exception as e:
            print(str(e))
            if imageid==None:
                raise("Vui lòng kiểm tra lại mật khẩu hoặc cấu hình website của bạn không phù hợp") 

        Text_replace_doc = {}
        Text_replace1 = []
        if len(Text_replace)>0:
            for i in Text_replace:
                j = i.split("|")
                if len(j)>=2:
                    Text_replace1.append(i)
                    Text_replace_doc[j[0]] = j[1]
        Blacklists = []

        for i in Blacklist:
            if "http" not in i:
                Blacklists.append(i)
            else:
                i = i.replace("https://","")
                Blacklists.append(i.replace("http://",""))



        website_infor = { 
            "UserId":UserId,
            "Email":Email,
            "Phone":Phone,
            "Website":website,
            "WebsitePost":website+"/wp-json/wp/v2/posts",
            "Type": "Basic" if Type=='' or Type==None else Type,
            "UserWP": UserWP,
            "PasswordWP": PasswordWP,
            "CampaignId":None,
            "TimeLastRun":0.0,
            "imageid":imageid,
            "Active":False,
            "StartActiveTime":None,
            "EndActiveTime":None,
            "Blacklist":Blacklists,
            "Phone_replace":Phone_replace,
            "Email_replace":Email_replace,
            "Text_replace":Text_replace,
            "Text_replace_doc":Text_replace_doc
        }
        try:
            inserted_id = str(self.website.insert_one(website_infor).inserted_id)
            website_infor["_id"] = inserted_id
            return website_infor
        except:
            raise(HTTPException(status_code=HTTP_404_NOT_FOUND,detail='Connect database fail'))

    def GetListUserWebsites(self,UserId,page:int,size:int):
        if size <= 0 or page<= 0:
            raise(HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="information is invalided"))
        total_page = math.ceil(float(self.website.count({"UserId":UserId}))/size)
        if page == 1:
            list_raw_website = self.website.find({"UserId":UserId}).limit(size)
            list_website = []
            for i in list_raw_website:
                i["_id"] = str(i["_id"])
                list_website.append(i)
            list_website = {
                "totalpage":total_page,
                "listwebsite":list_website,
                "currentpage":page,
                "totalsize":self.website.count({"UserId":UserId}),
                "sizepage":size
            }
        else:
            list_raw_website = []
            if page>1 and page<=total_page:
                list_raw_website = self.website.find().skip((page-1)*size).limit(size)
            list_website = []
            for i in list_raw_website:
                i["_id"] = str(i["_id"])
                list_website.append(i)
            list_website = {
                "totalpage":total_page,
                "listwebsite":list_website,
                "currentpage":page,
                "totalsize":self.website.count(),
                "sizepage":size
            }
        return list_website

    def GetWebsite(self,userid,websiteid):
        website = self.website.find_one({"_id":ObjectId(websiteid),"UserId":userid})
        website["_id"] = str(website["_id"])
        return website

    def UpdateWebsite(self,WebsiteId,UserId:str,Email:str,Phone:str,UserWP:str,PasswordWP:str,Phonereplace:str,Emailreplace:str,Text_replace:str,Blacklist:str):
        Text_replace_doc = {}
        Text_replace1 = []
        if len(Text_replace)>0:
            for i in Text_replace:
                j = i.split("|")
                if len(j)>=2:
                    Text_replace1.append(i)
                    Text_replace_doc[j[0]] = j[1]
        Blacklists = []

        for i in Blacklist:
            if "http" not in i:
                Blacklists.append(i)
            else:
                Blacklists.append(urlparse(i).netloc)

        myquery = { "UserId": UserId,"_id":ObjectId(WebsiteId)}
        newvalues = { "$set":{ 
            "Email":Email,
            "Phone":Phone,
            "UserWP": UserWP,
            "PasswordWP": PasswordWP,
            "Phone_replace":Phonereplace,
            "Email_replace":Emailreplace,
            "Text_replace":Text_replace,
            "Blacklist":Blacklists,
            "Text_replace_doc":Text_replace_doc

        }}
            
        website  = self.website.update_one(myquery, newvalues)
        return True

    def getallwebsite(self,page:int,size:int):
        if size <= 0 or page<= 0:
            raise(HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="information is invalided"))
        total_page = math.ceil(float(self.website.count())/size)
        if page == 1:
            list_raw_website = self.website.find().limit(size)
            list_website = []
            for i in list_raw_website:
                i["_id"] = str(i["_id"])
                list_website.append(i)
            list_website = {
                "totalpage":total_page,
                "listwebsite":list_website,
                "currentpage":page,
                "totalsize":self.website.count(),
                "sizepage":size
            }
        else:
            if page>1 and page<=total_page:
                list_raw_website = self.website.find().skip((page-1)*size).limit(size)
            list_website = []
            for i in list_raw_website:
                i["_id"] = str(i["_id"])
                list_website.append(i)
            list_website = {
                "totalpage":total_page,
                "listwebsite":list_website,
                "currentpage":page,
                "totalsize":self.website.count(),
                "sizepage":size
            }
        return list_website

    def getwebsitesbyname(self,UserId,websitename:str,page,size):
        if UserId =="admin":
            if size <= 0 or page<= 0:
                raise(HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="information is invalided"))
            total_page = math.ceil(float(self.website.count({"Website":websitename}))/size)
            if page == 1:
                list_raw_website = self.website.find({"Website":websitename}).limit(size)
                list_website = []
                for i in list_raw_website:
                    i["_id"] = str(i["_id"])
                    list_website.append(i)
                list_website = {
                    "totalpage":total_page,
                    "listwebsite":list_website,
                    "currentpage":page,
                    "totalsize":self.website.count(),
                    "sizepage":size
                }
            else:
                if page>1 and page<total_page:
                    list_raw_website = self.website.find({"Website":websitename}).skip((page-1)*size).limit(size)
                list_website = []
                for i in list_raw_website:
                    i["_id"] = str(i["_id"])
                    list_website.append(i)
                list_website = {
                    "totalpage":total_page,
                    "listwebsite":list_website,
                    "currentpage":page,
                    "totalsize":self.website.count(),
                    "sizepage":size
                }
            return list_website
        else:
            if size <= 0 or page<= 0:
                raise(HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="information is invalided"))
            total_page = math.ceil(float(self.account.count())/size)
            if page == 1:
                list_raw_website = self.website.find({"UserId":UserId,"Website":websitename}).limit(size)
                list_website = []
                for i in list_raw_website:
                    i["_id"] = str(i["_id"])
                    list_website.append(i)
                list_website = {
                    "totalpage":total_page,
                    "listwebsite":list_website,
                    "currentpage":page,
                    "totalsize":self.website.count(),
                    "sizepage":size
                }
            else:
                if page>1 and page<total_page:
                    list_raw_website = self.website.find({"UserId":UserId,"Website":websitename}).skip((page-1)*size).limit(size)
                list_website = []
                for i in list_raw_website:
                    i["_id"] = str(i["_id"])
                    list_website.append(i)
                list_website = {
                    "totalpage":total_page,
                    "listwebsite":list_website,
                    "currentpage":page,
                    "totalsize":self.website.count(),
                    "sizepage":size
                }
            return list_website

    def activewebsite(self,websiteid,times=1):
        myquery = {"_id":ObjectId(websiteid)}
        website = self.website.find_one({"_id":ObjectId(websiteid)})

        myquery = { "_id":ObjectId(websiteid)}
        if website["Active"]:
            newvalues = { "$set":{
                "Active":False,
                "StartActiveTime":None,
                "EndActiveTime":None
            }}
        else:
            newvalues = { "$set":{
                "Active":True,
                "StartActiveTime":time.time(),
                "EndActiveTime":float(time.time())+2592000*int(times)
            }}

        website  = self.website.update_one(myquery, newvalues)
        return True

    def addtimeactivewebsite(self,websiteid,times=1):
        myquery = {"_id":ObjectId(websiteid)}
        website = self.website.find_one({"_id":ObjectId(websiteid),"Active":True})
        if website!=None:
            myquery = { "_id":ObjectId(websiteid),"Active":True}
            newvalues = { "$set":{
                    "Active":True,
                    "EndActiveTime":website["EndActiveTime"]+2592000*int(times)
            }}
            website  = self.website.update_one(myquery, newvalues)
            return True
        else:
            return False
    def DeleteWebsite(self,UserId,websiteid):
        self.website.find_one_and_delete({"_id":ObjectId(websiteid),"UserId":UserId})
        return True

    def DeleteWebsiteByAdmin(self,websiteid):
        self.website.find_one_and_delete({"_id":ObjectId(websiteid)})
        return True
