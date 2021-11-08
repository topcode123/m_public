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




class  ImportContentToWP:
    def __init__(self) -> None:
        self.executor = ThreadPoolExecutor() # Or ProcessPoolExecutor
        self.results = []
        self.client = MongoClient(CONNECTION_STRING_MGA1)
        #self.client.drop_database("content")
        self.db1 = self.client.content
    def restImgUL(self,website,user,password,urlimg):
        if urlimg ==None:
            image = open("articlewriting1.jpg", "rb").read()
        else:
            path_files = urlimg.split("/")[-1]
            r = requests.get(urlimg)
            image = Image.open(io.BytesIO(r.content))
            image = image.resize((900,603))
            output = io.BytesIO()
            if path_files.split('.')[-1].upper()=="JPG":
                image.save(output,format='JPEG')
            else:
                image.save(output,path_files.split('.')[-1])
            image = output.getvalue()
        res = requests.post(website,
                            data=image,
                            headers={ 'Content-Type': 'image/jpg','Content-Disposition' : 'attachment; filename=%s'%path_files},
                            auth=(user, password))
        newDict=res.json()
        newID= newDict.get('id')
        link = newDict.get('guid').get("rendered")

        return newID
    def import_content(self, content):
        cl = self.client.user["userdatabase"].find_one({'_id':ObjectId(content['UserId'])})
        website = cl["Website"]
        websiteimg  = website.replace("/wp-json/wp/v2/posts","/wp-json/wp/v2/media")
        user = cl["UserWP"]
        password = cl["PasswordWP"]
        idthump = self.restImgUL(websiteimg,user,password,content['url_img'])
        credentials = user + ':' + password
        token = base64.b64encode(credentials.encode())
        header = {'Authorization': 'Basic ' + token.decode(')utf-8'),'Content-Type': 'application/json'}
        post = {
            'status': 'publish', 
            "title":content["title"],
            "content":content["content"],
            'categories':int(content["category"]),
            'featured_media':int(idthump),
            'slug': content['slug'] 

        }
        responce = requests.post(website , headers=header,json = post)
        print(website)

        print(responce.status_code)
        return responce.status_code
    
    def MultiThreadImportContent(self):
        listurl= []

        with self.db1.watch()  as stream:
            while stream.alive:
                
                listCollections = self.db1.collection_names({})

                while len(listCollections)>0:
                    listCollections = self.db1.collection_names({})

                    for i in listCollections:
                        if self.db1[i].count_documents({})>0:
                            a = self.db1[i].find_one_and_delete({})
                            listurl.append(a)
                    break
                if len(listurl)>0:
                    self.executor.map(self.import_content,listurl)
                listurl= []
ImportContentToWP().MultiThreadImportContent()