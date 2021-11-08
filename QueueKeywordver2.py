from sys import prefix
from bson.objectid import ObjectId
from pymongo import MongoClient
from Settings import *
import time

class QueueKeyword:

    def __init__(self) -> None:
        client = MongoClient(CONNECTION_STRING_MGA1)
        self.website  = MongoClient(CONNECTION_STRING_MGA1).websites.websiteconfig
        self.campaign  = MongoClient(CONNECTION_STRING_MGA1).campaigns.data
        self.cl = MongoClient(CONNECTION_STRING_MGA1).queuekeywords.data
        self.keywords  = MongoClient(CONNECTION_STRING_MGA1).keywords

        # client.drop_database("url")
        # client.drop_database("keywords")
        # self.cl.drop()
        self.dbtimes = client.times

    
    def ListenDataFromClient(self):
        with self.website.watch()  as stream:
            while stream.alive:
                # We end up here when there are no recent changes.
                # Sleep for a while before trying again to avoid flooding
                # the server with getMore requests when no changes are
                # available.
                for i in self.website.find({"Active":True}):
                    if i["TimeLastRun"]+ 60 <=time.time() and i["CampaignId"]!=None:
                        
                        campaign = self.campaign.find_one({"_id":ObjectId(i["CampaignId"])})
                        if campaign!=None and campaign["status"]:
                            if campaign["KeywordPerDay"]>0:
                                if i["TimeLastRun"] + int(60*1440/campaign["KeywordPerDay"])<=time.time():
                                    i["TimeLastRun"] = time.time()
                                    keyword = self.keywords[campaign["WebsiteId"]].find_one({"status":"waiting run","campaignid":i["CampaignId"]})
                                    if keyword!=None:
                                        self.keywords[campaign["WebsiteId"]].update_one({"_id":ObjectId(keyword["_id"])},{"$set":{"status":"pending"}})
                                        data = {
                                            "web_info":i,
                                            "campaign":campaign,
                                            "keyword":keyword
                                        }
                                        self.cl.insert(data)
                                        self.website.update_one({"_id":ObjectId(i["_id"])},{"$set":i})
                                        self.campaign.update_one({"_id":ObjectId(campaign["_id"])},{"$set":campaign})

                                        print(i["Website"])
QueueKeyword().ListenDataFromClient()