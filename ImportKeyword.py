from pymongo import MongoClient

from Settings import *


class ImportKeyword:

    def __init__(self) -> None:
        self.client = MongoClient(CONNECTION_STRING_MGA1)
        self.db =self.client.keywords_test

    def KeywordImportToCollection(self,ListKeys:list,id):
        collection = self.db[id]
        list_key = []
        for key in  ListKeys:
            list_key.append(key)
            if len(list_key)==10:
                collection.insert_many(list_key)
                list_key =[]
        if len(list_key)>0:
            collection.insert_many(list_key)



