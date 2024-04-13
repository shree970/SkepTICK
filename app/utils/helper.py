import os
import openai
from dotenv import load_dotenv
import pymongo
import pymongo.collection
from app.config.models import MongoClient, TranscribeResponse
from langdetect import detect
from pytube import YouTube, extract
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound


load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def mongo_client():
    mongo_config = MongoClient()
    client = pymongo.MongoClient(mongo_config.mongo_uri)
    db = client.get_database(mongo_config.dbname)
    collection = db.get_collection(mongo_config.collection_name)
    return collection


def transcribe(video_url: str) -> TranscribeResponse:
    """
    Given YouTube Video URL as input, returns the transcription
    :param video_url:
    :return: <str> transcribed text and author name
    """
    try:
        youtube = YouTube(video_url)
        description = youtube.description
        title = youtube.title

        transcript = ""
        video_id = extract.video_id(video_url)
        srt = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])

        for line in srt:
            transcript = transcript + " " + line["text"]

        lang_code = detect(transcript)

        return TranscribeResponse(video_id=video_id,
                                  lang_code=lang_code,
                                  title=title,
                                  description=description,
                                  transcript=transcript)
    except NoTranscriptFound:
        video_id = extract.video_id(video_url)
        return TranscribeResponse(video_id=video_id)
