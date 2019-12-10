from pymongo import MongoClient
import pandas as pd
import json

class client:
    def __init__(self, host='localhost', port=27017):
        self.client = MongoClient(host,port)
        self.db = self.client['sentimentdb']

    def insert(self, topic, mydict):
        coll = self.db[topic]
        coll.insert_one(mydict)
        return coll.count_documents({})

    def insertmany(self, topic, dataFrame):
        self.dataFrame_json = dataFrame.T.to_json()
        self.dataFrame_json_list = json.loads(self.dataFrame_json).values()
        coll = self.db[topic]
        coll.insert_many(self.dataFrame_json_list)
        return coll.count_documents({})

    def retrieve(self, topic='keywords'):
        coll = self.db[topic]
        exclude_col = {'_id': False }
        data = list(coll.find({}, projection=exclude_col))
        df = pd.DataFrame(data, columns=['keyword', 'num'])
        return df

    def retrieveByValue(self,topic='tweets', keyword=''):
        coll = self.db[topic]
        exclude_col = {'_id': False }
        myquery = { "keyword": keyword }
        data = list(coll.find(myquery, projection=exclude_col))
        df = pd.DataFrame(data, columns=['date','tweet', 'username','sentiment'])
        return df

    def deleteall(self, topic):
        coll = self.db[topic]
        coll.delete_many({})

    def deleteByValue(self, keyword):
        coll1 = self.db['tweets']
        coll2 = self.db['keywords']
        myquery = { "keyword": keyword }
        coll1.delete_many(myquery)
        coll2.delete_many(myquery)

    def update(self, topic, fieldname ):
        coll = self.db[topic]
        coll.update_many({}, {"$unset": {fieldname:""}} )
