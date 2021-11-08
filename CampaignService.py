from datetime import datetime, time, timedelta
from typing import Optional
import fastapi
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from newspaper.api import languages
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
import json
import hashlib
class Campaign(BaseModel):
    namecampaign:str
    userid:str
    websiteid:str
    website:str
    listkeyword:list
    categoryid:int
    categoryname:str
    categorylink:str
    keywordperday:int
    starttime:datetime
    endtime:datetime
    language:str

class CampaignService:
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
        self.campaign  = MongoClient(CONNECTION_STRING_MGA1).campaigns.data
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.website  = MongoClient(CONNECTION_STRING_MGA1).websites.websiteconfig
        self.keywords  = MongoClient(CONNECTION_STRING_MGA1).keywords



    #Thêm mới website
    def AddCampaign(self,namecampaign:str,userid:str,websiteid:str,listkeyword:list,categoryid:int,categoryname:str,categorylink:str,top10url:list,KeywordPerDay:int,starttime:datetime,endtime:datetime,website,language):
        '''
        Token: Tài khoản sau khi login sẽ tạo ra một token để dùng xác thực cho các api sau này.
        UserWP: Là thông tin username đăng nhập vào hệ thống wp-admin.
        Password WP: là thông tin về mật khẩu của ứng dụng.
        Response:+ Nếu chưa đăng nhập hoặc token hết hạn sẽ báo lỗi 401 unauthorized
                + Nếu xác thực thông tin đăng nhập thành công thì sẽ cho tạo website và lúc này Active = False đợi admin xác thực.
                + Process là id chiến dịch mà hệ website đang chạy
        '''
        campaign_infor = {
            "Name":namecampaign,
            "UserId":userid,
            "WebsiteId":websiteid,
            "Website":website,
            "CategoryId": categoryid,
            "CategoryName": categoryname,
            "CategoryLink": categorylink,
            "Top10url": top10url,
            "status" : False,
            "StartTime":starttime,
            "EndTime": endtime,
            "KeywordPerDay":KeywordPerDay if KeywordPerDay!=None or (KeywordPerDay<1440 and KeywordPerDay>-1) else 1440,
            "language": language,
        }
        try:
            inserted_id = str(self.campaign.insert_one(campaign_infor).inserted_id)
            campaign_infor["_id"] = inserted_id
            listkeywords = []
            for i in listkeyword:
                a = {
                    "Keyword":i,
                    "status":"waiting run",
                    "link": None,
                    "campaignid":inserted_id
                }
                listkeywords.append(a)
            self.keywords[websiteid].insert_many(listkeywords)
            return campaign_infor
        except:
            raise(HTTPException(status_code=HTTP_404_NOT_FOUND,detail='Connect database fail'))

    def GetAllCategories(self,website):
        all_category = requests.get(website+"/wp-json/wp/v2/categories?page=1&per_page=100",allow_redirects=False,verify=False,timeout=50).content
        hh = json.loads(all_category)
        categories = []
        for i in hh:
            m = {"id":i["id"],
                "link":i["link"],
                "name":i["name"]}
            categories.append(m)
        return categories

    def GetTopUrl(self,website,categoryid):
        all_url = requests.get("{}/wp-json/wp/v2/posts?categories={}".format(website,categoryid),allow_redirects=False,verify=False,timeout=50).content
        hh = json.loads(all_url)
        urllist = []
        for i in hh:
            m = {"link":i["link"],
                "name":i["title"]["rendered"]}
            urllist.append(m)

        return urllist

    def ResetCampaign(self,campaignid):
        filter = { "_id":ObjectId(campaignid) }

        newvalues = { "$set": { 'index': 0,"KeyDone": []} }
    
        campaign  = self.campaign.update_one(filter, newvalues)
        self.StopCampaign(campaignid)
        return True

    def StartCampaign(self,campaignid1):
        filter = { "_id":ObjectId(campaignid1) }
        campaignid = self.campaign.find_one(filter)["WebsiteId"]
        WebsiteId = self.website.find_one({ "_id":ObjectId(campaignid) })
        if WebsiteId["CampaignId"] != campaignid:
            CampaignId = self.campaign.update_one( {"_id":ObjectId(WebsiteId["CampaignId"]) },{"$set": { "status": False} })
            WebsiteId = self.website.update_one({ "_id":ObjectId(campaignid) },{ "$set": { "CampaignId": campaignid1} })
            CampaignId = self.campaign.update_one(filter,{"$set": { "status": True} })
        return True

    def StopCampaign(self,campaignid):
        filter = { "_id":ObjectId(campaignid) }
        WebsiteId = self.campaign.find_one(filter)["WebsiteId"]
        WebsiteId = self.website.find_one({ "_id":ObjectId(WebsiteId) })
        if WebsiteId["CampaignId"] == campaignid:
            WebsiteId = self.website.update_one({ "_id":ObjectId(campaignid) },{ "$set": { "CampaignId": None} })
            CampaignId = self.campaign.update_one(filter,{"$set": { "status": False} })
        return True
    
    def UpdateCampaign(self,campaignid:str,userid:str,categoryid:int,categoryname:str,categorylink:str,top10url:list,KeywordPerDay:int,starttime:datetime,endtime:datetime,language,websiteid:str,campaignname,listkeyword:Optional[list]=[]):
        myquery = { "UserId": userid,"_id":ObjectId(campaignid)}
        newvalues = { "$set":{ 
            "Name":campaignname,
            "UserId":userid,
            "CategoryId": categoryid,
            "CategoryName": categoryname,
            "CategoryLink": categorylink,
            "StartTime":starttime,
            "EndTime": endtime,
            "Top10url": top10url,
            "KeywordPerDay":KeywordPerDay if KeywordPerDay!=None or KeywordPerDay>1440 else 1440,
            "language" : language

        }}
        listkeywords = []
        for i in listkeyword:
            a = {
                "Keyword":i,
                "status":"waiting run",
                "link": None,
                "campaignid":campaignid
            }
            listkeywords.append(a)
        if len(listkeywords)>0:
            self.keywords[websiteid].insert_many(listkeywords)
        website  = self.campaign.update_one(myquery, newvalues)
        
        return True

    def DeleteCampaign(self,campaignid):
        filter = { "_id":ObjectId(campaignid) }
        WebsiteId = self.campaign.find_one_and_delete({ "_id":ObjectId(campaignid)})
        return True
    
    def GetCampaign(self,campaignid):
        filter = { "_id":ObjectId(campaignid) }
        WebsiteId = self.campaign.find_one({ "_id":ObjectId(campaignid)})
        WebsiteId["_id"] = str(WebsiteId["_id"]) 
        return WebsiteId

    def GetListKeyword(self,WebsiteId:str,Campaignid:str,size:int,page:int,status:Optional[str]=None):
        if status==None:
            if size <= 0 or page<= 0:
                raise(HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="information is invalided"))
            list_campaign = None
            total_page = math.ceil(float(self.keywords[WebsiteId].count({"campaignid":Campaignid,}))/size)
            if page == 1:
                list_campaign_test = self.keywords[WebsiteId].find({"campaignid":Campaignid}).limit(size)
                list_campaign = []
                for i in list_campaign_test:
                    i["_id"] = str(i["_id"])
                    list_campaign.append(i)

                list_campaign = {
                    "totalpage":total_page,
                    "listaccount":list_campaign,
                    "currentpage":page,
                    "totalsize":self.keywords[WebsiteId].count({"campaignid":Campaignid}),
                    "sizepage":size
                }
            else:
                list_campaign = []
                list_campaign_test = []
                if page>1 and page<=total_page:
                    list_campaign_test = self.keywords[WebsiteId].find({"campaignid":Campaignid}).skip((page-1)*size).limit(size)
                for i in list_campaign_test:
                    i["_id"] = str(i["_id"])
                    list_campaign.append(i)
                list_campaign = {
                    "totalpage":total_page,
                    "listaccount":list_campaign,
                    "currentpage":page,
                    "totalsize":self.keywords[WebsiteId].count({"campaignid":Campaignid}),
                    "sizepage":size
                }

            return list_campaign
        else:
            if size <= 0 or page<= 0:
                raise(HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="information is invalided"))
            list_campaign = None
            total_page = math.ceil(float(self.keywords[WebsiteId].count({"campaignid":Campaignid,"status":status}))/size)
            if page == 1:
                list_campaign_test = self.keywords[WebsiteId].find({"campaignid":Campaignid,"status":status}).limit(size)
                list_campaign = []
                for i in list_campaign_test:
                    i["_id"] = str(i["_id"])
                    list_campaign.append(i)

                list_campaign = {
                    "totalpage":total_page,
                    "listaccount":list_campaign,
                    "currentpage":page,
                    "totalsize":self.campaign.count({"campaignid":Campaignid,"status":status}),
                    "sizepage":size
                }
            else:
                if page>1 and page<total_page:
                    list_campaign_test = self.campaign.find({"campaignid":Campaignid,"status":status}).skip((page-1)*size).limit(size)
                list_campaign = []
                for i in list_campaign_test:
                    i["_id"] = str(i["_id"])
                    list_campaign.append(i)
                list_campaign = {
                    "totalpage":total_page,
                    "listaccount":list_campaign,
                    "currentpage":page,
                    "totalsize":self.campaign.count({"campaignid":Campaignid,"status":status}),
                    "sizepage":size
                }
            return list_campaign

    def GetListCampaign(self,WebsiteId,size:int,page:int):
        if size <= 0 or page<= 0:
            raise(HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="information is invalided"))
        list_campaign = None
        total_page = math.ceil(float(self.campaign.count({"WebsiteId":WebsiteId}))/size)
        if page == 1:
            list_campaign_test = self.campaign.find({"WebsiteId":WebsiteId}).limit(size)
            list_campaign = []
            for i in list_campaign_test:
                i["_id"] = str(i["_id"])
                list_campaign.append(i)

            list_campaign = {
                "totalpage":total_page,
                "listaccount":list_campaign,
                "currentpage":page,
                "totalsize":self.campaign.count({"WebsiteId":WebsiteId}),
                "sizepage":size
            }
        else:
            list_campaign_test = []
            list_campaign = []
            if page>1 and page<=total_page:
                list_campaign_test = self.campaign.find({"WebsiteId":WebsiteId}).skip((page-1)*size).limit(size)
            for i in list_campaign_test:
                i["_id"] = str(i["_id"])
                list_campaign.append(i)
            list_campaign = {
                "totalpage":total_page,
                "listaccount":list_campaign,
                "currentpage":page,
                "totalsize":self.campaign.count({"WebsiteId":WebsiteId}),
                "sizepage":size
            }
        return list_campaign


