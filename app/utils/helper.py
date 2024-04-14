import os

import openai
import pymongo
import pymongo.collection
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langdetect import detect
from pytube import YouTube, extract
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound

from app.config.models import MongoClient, TranscribeResponse

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
        description = get_description(video_url)
        title = get_title(video_url)

        transcript = ""
        video_id = extract.video_id(video_url)
        srt = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])

        for line in srt:
            transcript = transcript + " " + line["text"]

        lang_code = detect(transcript)

        return TranscribeResponse(
            video_id=video_id,
            lang_code=lang_code,
            title=title,
            description=description,
            transcript=transcript,
        )
    except NoTranscriptFound:
        video_id = extract.video_id(video_url)
        return TranscribeResponse(video_id=video_id)


def get_title(video_url: str) -> str:
    r = requests.get(video_url)
    soup = BeautifulSoup(r.text)

    link = soup.find_all(name="title")[0]
    title = str(link)
    title = title.replace("<title>", "")
    title = title.replace("</title>", "")

    return title


def get_description(video_url):
    yt = YouTube(video_url)
    for n in range(6):
        try:
            description = yt.initial_data["engagementPanels"][n][
                "engagementPanelSectionListRenderer"
            ]["content"]["structuredDescriptionContentRenderer"]["items"][1][
                "expandableVideoDescriptionBodyRenderer"
            ][
                "attributedDescriptionBodyText"
            ][
                "content"
            ]
            return description
        except Exception as exp:
            print(f"Exception occured while getting video description: {exp}")
            continue
    return False
