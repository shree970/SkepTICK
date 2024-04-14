from pymongo.errors import DuplicateKeyError

from app.utils.helper import mongo_client


class MongoDB:
    def __init__(self):
        self.collection = mongo_client()

    def create(self, data):
        try:
            result = self.collection.insert_one(data)
            return result.inserted_id
        except DuplicateKeyError:
            return None

    def read(self, query=None):
        if query is None:
            query = {}
        return self.collection.find_one(query)

    def update(self, query, new_data):
        result = self.collection.update_one(query, {"$set": new_data})
        return result.modified_count

    def delete(self, query):
        result = self.collection.delete_one(query)
        return result.deleted_count
