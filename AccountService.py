from datetime import datetime, time, timedelta
from typing import Optional
import fastapi
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from pydantic.types import Json
from Settings import *
from pymongo import MongoClient
from bson import ObjectId
from urllib.parse import urlparse
from typing import Optional
import math
import hashlib
class Account(BaseModel):
    username:str
    password:str
    email:str
class AccountService:
    """
    database in mongodb: Account
    - username
    - email
    - password 
    """
    def __init__(self) -> None:
        self.account  = MongoClient(CONNECTION_STRING_MGA1).accounts.data
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # Tạo mới tài khoản
    def AddAccount(self,account:Account): #cần thông tin email và password
        if self.account.count({'username': account.username}, limit = 1) != 0:
            raise(HTTPException(status_code=status.HTTP_409_CONFLICT,detail="username has existed",))
        if self.account.count({'email': account.username}, limit = 1) != 0:
            raise(HTTPException(status_code=status.HTTP_409_CONFLICT,detail="username has existed",))
        if len(account.username)<3:
            raise(HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="username is too short",))
        if len(account.email)<5 or "@" not in account.email or "." not in account.email:
            raise(HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="email is Invalided",))
        if len(account.password)<8:
            raise(HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="your password is too short",))
        try:
            new_account = {
                "username":account.username,
                "email":account.email,
                "password":hashlib.md5(account.password.encode('utf8')).hexdigest(),
                "type":"client"
            }
            inserted_id = str(self.account.insert_one(new_account).inserted_id)
            return inserted_id
        except:
            raise(HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,detail="connect to server is interrupted",))


    # Đăng nhập tài khoản
    def Login(self,email:str,password:str):
        if email == "" or len(password)<8:
            raise(HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="information is invalided",))
        account = self.account.find_one({"username":email})
        if account!=None:
            pass 
        else:
            account = self.account.find_one({"email":email})
            if not account:
                raise(HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Incorrect email or username",))
        if (account["password"]!= hashlib.md5(password.encode('utf8')).hexdigest()):
            raise(HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Incorrect Password",))
        else:
            return account
    
    def ChangePassword(self,userid,old_password:str,new_password:str):
        if old_password == new_password:
            raise(HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="new password same old password"))
        if len (new_password)<8:
            raise(HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="new password is too short"))
        if self.account.find_one({"_id":ObjectId(userid)})["password"] != self.pwd_context.hash(old_password):
            raise(HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="your password not match"))
        else:
            filter = { "_id":ObjectId(userid) }
  
            # Values to be updated.
            newvalues = { "$set": { 'password': hashlib.md5(new_password.encode('utf8')).hexdigest() } }
            
            # Using update_one() method for single 
            # updation.
            account  = self.account.update_one(filter, newvalues)
            return account

    def GetListAccount(self,page:int,size:int):
        if size <= 0 or page<= 0:
            raise(HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="information is invalided"))
        list_account = None
        total_page = math.ceil(float(self.account.count())/size)
        if page == 1:
            list_account_test = self.account.find().limit(size)
            list_account = []
            for i in list_account_test:
                i["_id"] = str(i["_id"])
                list_account.append(i)

            list_account = {
                "totalpage":total_page,
                "listaccount":list_account,
                "currentpage":page,
                "totalsize":self.account.count(),
                "sizepage":size
            }
        else:
            list_account_test = []
            if page>1 and page<=total_page:
                list_account_test = self.account.find().skip((page-1)*size).limit(size)
            list_account = []
            for i in list_account_test:
                i["_id"] = str(i["_id"])
                list_account.append(i)
            list_account = {
                "totalpage":total_page,
                "listaccount":list_account,
                "currentpage":page,
                "totalsize":self.account.count(),
                "sizepage":size
            }
        return list_account

    def DeleteAccount(self,id:str):
        try:
            self.account.delete_one({'_id':ObjectId(id)})
            return True
        except:
            return False
    #hàm chức năng tạo accesstoken
    def CreateAccessToken(self, data, expires_delta: Optional[timedelta] = None):
        '''
        AccessToken có thời gian tối đa là 300 phút tương đương 100 ngày.
        SECRET_KEY và ALGORITHM để trong file settings.py của hệ thống.
        '''
        to_encode = data
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=600)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    #hàm chức năng khởi tạo accesstoken khi login tài khoản 
    def LoginGetAccessToken(self,email,password):
        user = self.Login(email, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user["_id"] = str(user["_id"])
        print(user)

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.CreateAccessToken(
            data=user, expires_delta=access_token_expires
        )
        return {"access_token": access_token,"userid":str(user["_id"]),"username":user["username"],"email":user["email"],"type":user["type"], "token_type": "bearer"}
    
    def GetCurrentUser(self,token):
        '''
        Giải mã AccessToken để xác thực thông tin tài khoản. 
        '''
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            payload["_id"] = str(payload["_id"])
            if payload is None:
                raise credentials_exception
        except:
            raise credentials_exception
        return payload
