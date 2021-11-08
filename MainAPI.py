from re import A
from typing import Optional
from datetime import datetime
from fastapi import HTTPException, status,Depends
from fastapi import FastAPI, File, UploadFile,Form
from pydantic.main import BaseModel
from starlette.status import HTTP_404_NOT_FOUND

from AccountService import *
from fastapi import Depends, FastAPI, HTTPException, status,File,Form,Request,Response, BackgroundTasks

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from CampaignService import Campaign, CampaignService
from ImportKeyword import ImportKeyword
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os 
import time
from fastapi_mail import FastMail, MessageSchema,ConnectionConfig
import random
import string
from WebsiteService import *

def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str



from urllib.parse import urlparse
account  = MongoClient(CONNECTION_STRING_MGA1).accounts.data
app = FastAPI()
userapi = FastAPI()
accountService =  AccountService()
websiteService = WebsiteService()
campaignservice  = CampaignService()
origins = ['*']
adminapi = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@userapi.middleware("http")
async def check_user_header(request: Request, call_next):
    response = Response(status_code=401,content="Unauthorized")
    if request["path"] == "/docs" or request["path"] == "/openapi.json":
        b = await call_next(request)
    else:
        a = None
        try:
            a = accountService.GetCurrentUser(request.headers["access-token"])
            # if(request.query_params["userid"]!= a["_id"] and "campaign" not in request["path"]):
            #     return response
        except:
            return response
        b = await call_next(request)
    return b
@adminapi.middleware("http")
async def check_user_header(request: Request, call_next):
    response = Response(status_code=401,content="Unauthorized")
    if request["path"] == "/docs" or request["path"] == "/openapi.json":
        b = await call_next(request)
    else:
        a = None
        try:
            a = accountService.GetCurrentUser(request.headers["access-token"])
            if a["type"]!= "admin":
                return response
        except:
            return response
        b = await call_next(request)
    return b
class AccountLogin(BaseModel):
    usernameoremail: str
    password: str

class AccountChangePassword(BaseModel):
    oldpassword: str
    newpassword: str
    
conf = ConnectionConfig(
    MAIL_USERNAME="vutrian576@gmail.com",
    MAIL_PASSWORD="an.vt1729333",
    MAIL_FROM="vutrian576@gmail.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_FROM_NAME="Mnetword",
    MAIL_TLS=True,
    MAIL_SSL=False,
    TEMPLATE_FOLDER='templates/'
)

"""
Các api quản lí tài khoản khách hàng:
+ Thay đổi mật khẩu
+ Quên mật khẩu qua email
+ tạo tài khoản mới
+ hiển thị list danh sách tài khoản (admin)
+ xóa một tài khoản (admin)
+ đăng nhập vào hệ thống
"""

#quên mật khẩu bằng cách sử dụng email
def send_email_background(background_tasks: BackgroundTasks, subject: str, email_to: str, body: dict):
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        template_body=body,
        subtype='html')
    fm = FastMail(conf)
    background_tasks.add_task(
        fm.send_message, message, template_name='forgot_password.html')

@app.get('/send-email/getpassword')
def send_email_backgroundtasks(background_tasks: BackgroundTasks,email:str):
    filter = { "email":email }
    account  = MongoClient(CONNECTION_STRING_MGA1).accounts.data
    # Values to be updated.
    find= account.find_one(filter)
    print(find)
    if not find:
        raise(HTTPException(status_code=HTTP_404_NOT_FOUND,detail="Tài khoản không tồn tại trong hệ thống"))
    password = get_random_string(8)
    newvalues = { "$set": { 'password': hashlib.md5(password.encode('utf8')).hexdigest() } }
    user = account.find_one_and_update(filter,newvalues)
    name = email.split("@")[0]
    send_email_background(background_tasks, 'Khôi phục mật khẩu!', email, {'title': 'Khôi phục mật khẩu!', 'name':name, 'password':password})
    return 'Đã gửi thành công'

#Đăng nhập vào hệ thống
@app.post("/login")
async def LoginGetAccessToken(information_account:AccountLogin):
    infor = accountService.LoginGetAccessToken(information_account.usernameoremail,information_account.password)
    return infor

#đăng kí tài khoản hệ thống
@app.post("/register")
async def RegisterAccount(account:Account):
    infor = accountService.AddAccount(account)
    return infor

#thay đổi  mật khẩu hệ thống của user
@userapi.put("/changepassword")
async def ChangePassword(userid:str,accountChangePassword:AccountChangePassword):
    infor = accountService.ChangePassword(userid,accountChangePassword.oldpassword,accountChangePassword.newpassword)
    return infor

#thay đổi  mật khẩu hệ thống của admin
@adminapi.put("/changepassword/{userid}")
async def ChangePassword(userid:str,accountChangePassword:AccountChangePassword):
    infor = accountService.ChangePassword(userid,accountChangePassword.oldpassword,accountChangePassword.newpassword)
    return infor

#xóa một tài khoản user ra khỏi hệ thống
@adminapi.delete("/deleteacount/{userid}")
async def DeleteAccount(userid:str):
    infor = accountService.DeleteAccount(userid)
    return infor

#get list danh sách tài khoản khách hàng
@adminapi.get("/listacount")
async def GetAccount(page:int,size:int):
    infor = accountService.GetListAccount(page,size)
    return infor


"""
Các API quản lí website là:
+ Tạo mới một website (user)
+ Xóa một website (user+admin)
+ Thay đổi thông tin một website (user)
+ Active 1 website (admin)
+ Get list website theo user (user+admin)
+ Get list website (admin)
+ Get a website (admin + user)
+ Get listwebsite by namewebsite (admin + user)
"""
@userapi.post("/createwebsite")
async def CreateWebsite(userid:str,webinfor:Website):
    if "http" not in webinfor.Website:
        webinfor.Website = "https://"+webinfor.Website
    if webinfor.Website[-1] == "/":
        webinfor.Website = webinfor.Website[:-1]
    print(webinfor.Website)
    website = await websiteService.AddWebsite(userid,webinfor.Email,webinfor.Phone,webinfor.Website,webinfor.UserWP,webinfor.PasswordWP,webinfor.Blacklist,webinfor.Phone_replace,webinfor.Email_replace,webinfor.Text_replace)
    return website

@userapi.put("/updatewebsite")
async def UpdateWebsite(websiteid:str,userid:str,webinfor:Website):
    if "http" not in webinfor.Website:
        webinfor.Website = "https://"+webinfor.Website
    if webinfor.Website[-1] == "/":
        webinfor.Website = webinfor.Website[:-1]
    website = websiteService.UpdateWebsite(websiteid,userid,webinfor.Email,webinfor.Phone,webinfor.UserWP,webinfor.PasswordWP,webinfor.Phone_replace,webinfor.Email_replace,webinfor.Text_replace,webinfor.Blacklist)
    return website

@userapi.delete("/deletewebsite")
async def DeleteWebsite(websiteid:str,userid:str):
    website = websiteService.DeleteWebsite(userid,websiteid)
    return website

@userapi.get("/getwebsite")
async def GetWebsite(websiteid:str,userid:str):
    website = websiteService.GetWebsite(userid,websiteid)
    return website

@userapi.get("/getlistwebsites")
async def GetaWebsite(userid:str,page:int,size:int):
    website = websiteService.GetListUserWebsites(userid,page,size)
    return website

@adminapi.put("/active/{websiteid}")
async def ActiveWebsite(websiteid,times=1):
    return websiteService.activewebsite(websiteid,times)
@adminapi.put("/addtimeactive/{websiteid}")
async def ActiveWebsite(websiteid,times=1):
    a= websiteService.addtimeactivewebsite(websiteid,times)
    return a
@adminapi.get("/getlistwebsites")
async def GetListWebsite(page:int,size:int):
    return websiteService.getallwebsite(page,size)

@userapi.get("/getlistwebsites")
async def GetaWebsite(userid:str,page:int,size:int):
    website = websiteService.GetListUserWebsites(userid,page,size)
    return website

@userapi.post("/campaign/create")
async def CreateCampaign(campaign:Campaign):
    if "http" not in campaign.website:
        campaign.website = "https://"+campaign.website
        print(campaign.website)
    if campaign.website[-1] == "/":
        campaign.website = campaign.website[:-1]
    GetTopUrl = campaignservice.GetTopUrl(campaign.website,campaign.categoryid)
    Campaign = campaignservice.AddCampaign(campaign.namecampaign,campaign.userid,campaign.websiteid,campaign.listkeyword,campaign.categoryid,campaign.categoryname,campaign.categorylink,GetTopUrl,campaign.keywordperday,campaign.starttime,campaign.endtime,campaign.website,campaign.language)
    return Campaign
@userapi.post("/campaign/createwithfile")
async def CreateCampaign(namecampaign: str = Form(...),userid:str = Form(...),websiteid:str = Form(...),categoryid:str = Form(...),categoryname:str = Form(...),categorylink:str = Form(...),KeywordPerDay:int=Form(...),starttime:datetime=Form(...),endtime:datetime=Form(...),website:str=Form(...),language:str=Form(...),FileKeyWord: UploadFile = File(...)):
    if "http" not in website:
        website = "https://"+website
    if website[-1] == "/":
        website = website[:-1]
    if not os.path.isdir(os.path.join(os.getcwd(),"dataupload",str(websiteid))):
        os.mkdir(os.path.join(os.getcwd(),"dataupload",str(websiteid)))

    file_name = os.getcwd()+"/dataupload/{}/".format(str(websiteid))+str(time.time())+FileKeyWord.filename.replace(" ", "-")
    with open(file_name,'wb+') as f:
        Content = await FileKeyWord.read()
        f.write(Content)
        f.close()
    with open(file_name,'r',encoding="utf-8") as f:
        KeyWords = f.readlines()
    listkeywords = [i for i in KeyWords]
    GetTopUrl = campaignservice.GetTopUrl(website,categoryid)
    Campaign = campaignservice.AddCampaign(namecampaign,userid,websiteid,listkeywords,categoryid,categoryname,categorylink,GetTopUrl,KeywordPerDay,starttime,endtime,website,language)
    return Campaign
@userapi.put("/campaign/stop")
async def StopCampaign(campaignid:str):
    Campaign = campaignservice.StopCampaign(campaignid)
    return Campaign

@userapi.put("/campaign/start")
async def StartCampaign(campaignid:str):
    Campaign = campaignservice.StartCampaign(campaignid)
    return Campaign

@userapi.put("/campaign/reset")
async def ResetCampaign(campaignid:str):
    Campaign = campaignservice.ResetCampaign(campaignid)
    return Campaign

@userapi.put("/campaign/update")
async def UpdateCampaign(campaignid:str,campaign:Campaign):
    if "http" not in campaign.website:
        campaign.website = "https://"+campaign.website
    if campaign.website[-1] == "/":
        campaign.website = campaign.website[:-1]
    GetTopUrl = campaignservice.GetTopUrl(campaign.website,campaign.categoryid)
    Campaign = campaignservice.UpdateCampaign(campaignid,campaign.userid,campaign.categoryid,campaign.categoryname,campaign.categorylink,GetTopUrl,campaign.keywordperday,campaign.starttime,campaign.endtime,campaign.language,campaign.websiteid,campaign.listkeyword)
    return Campaign

@userapi.delete("/campaign/delete")
async def DeleteCampaign(campaignid:str):
    Campaign = campaignservice.DeleteCampaign(campaignid)
    return Campaign

@userapi.get("/campaign")
async def GetCampaign(campaignid:str):
    Campaign = campaignservice.GetCampaign(campaignid)
    return Campaign

@userapi.get("/listcampaign")
async def GetCampaign(WebsiteId,size:int,page:int):
    Campaign = campaignservice.GetListCampaign(WebsiteId,size,page)
    return Campaign
@userapi.get("/campaign/listkeywords")
async def GetCampaign(WebsiteId,campaignid,size:int,page:int,status=None):
    Campaign = campaignservice.GetListKeyword(WebsiteId,campaignid,size,page,status)
    return Campaign
@userapi.get("/website/category")
async def GetAllCategoryOfWebsite(website):
    category = campaignservice.GetAllCategories(website)
    return category


app.mount("/user", userapi)
app.mount("/admin", adminapi)
if __name__ == "__main__":
    uvicorn.run("MainAPI:app",host="0.0.0.0", port=8050,reload=True,forwarded_allow_ips="*")