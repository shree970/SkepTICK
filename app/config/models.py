import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class MongoClient(BaseModel):
    mongo_uri: str = Field(default=os.getenv('MONGO_URI'))
    dbname: str = Field(default=os.getenv("MONGO_DBNAME"))
    collection_name: str = Field(default=os.getenv("MONGO_COLLECTION"))


class GPT4Config(BaseModel):
    model_name: str = Field(default="gpt-3.5-turbo")
    temperature: float = Field(default=0.05)
    max_tokens: int = Field(default=1000)
    timeout: int = Field(default=120)


class TranscribeResponse(BaseModel):
    video_id: str
    lang_code: str = Field(default=None)
    title: str = Field(default=None)
    description: str = Field(default=None)
    transcript: str = Field(default=None)
