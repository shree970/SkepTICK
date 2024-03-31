"""
TODO:
1. check for english transcript availability in youtube api
2. Add binary classifier for only using finance videos.
    If false, return "This video is not about finance. Please provide a finance video."
3. Store the video claims and transcriptions in MongoDB -
    Table User:
    Age: int
    Risk_profile: str
    video_id: str
    feedback: str/ int
    client_information: dict

    Table VideoTranscription:
    video_id: str
    video_link: str
    claims: dict
    transcript: dict
    stock_names: list[str]
"""

import pymongo
import pymongo.collection
from dotenv import load_dotenv
from fastapi import APIRouter
from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langdetect import detect
from pytube import YouTube, extract
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_core.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from bson.objectid import ObjectId
from app.config.models import MongoClient, TranscribeRequest, GPT4Config, TranscribeResponse
from youtube_transcript_api._errors import NoTranscriptFound

load_dotenv()

router = APIRouter()


def transcribe(video_url):
    """
    Given YouTube Video URL as input, returns the transcription
    :param video_url:
    :return: <str> transcribed text and author name
    """
    try:
        youtube = YouTube(video_url)
        author = youtube.author
        description = youtube.description
        title = youtube.title

        transcript = ""
        video_id = extract.video_id(video_url)
        srt = YouTubeTranscriptApi.get_transcript(video_id, languages="en")

        for line in srt:
            transcript = transcript + " " + line["text"]

        lang_code = detect(transcript)

        return TranscribeResponse(video_id=video_id, lang_code=lang_code, title=title, description=description, transcript=transcript)
    except NoTranscriptFound:
        return TranscribeResponse(video_id=video_id, lang_code=None, title=title, description=description, transcript=None)


def content_filter(title, description):
    """
    title: Youtube Video Title
    description: Youtube Video Description
    return: bool (True or False)
    """
    openai_config = GPT4Config()
    chat = ChatOpenAI(
        temperature=openai_config.temperature,
        model_name=openai_config.model_name, 
        request_timeout=openai_config.timeout
        )
    
    template = (
    """
    You are a honest assistant. 
    You are provided with Youtube video title and description.
    Your task is to classify whether the title and description are related to any of the topics listed below
    [Finance, Financial Education, Financial Advice, Stock Markets, Stock Recommendation].
    Response should be strictly limited to either True or False. Do not include anything else in the response.
    """
    )
    system_message_prompt = SystemMessagePromptTemplate.from_template(template)
    human_template = "{title}, {description}"
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
    prompt = chat_prompt.format_prompt(title=title, description=description).to_messages()
    response = chat(prompt)
    return eval(response.content)


def extract_claims(transcript):
    """
    Takes YouTube transcript as input, extracts stock name, claims, theoretical and quantitative thesis
    :param transcript:
    :return: writes JSON files for theoretical and quantitative parts
    """

    openai_config = GPT4Config()
    chat = ChatOpenAI(
        temperature=openai_config.temperature,
        model_name=openai_config.model_name, 
        request_timeout=openai_config.timeout
        )
    
    messages = [
        SystemMessage(content="""
        You are a Financial Analyst. Your task is to identify the company stock and the context of claims made on the stock by a Financial Influencer. 
        Please separate out the theoretical and quantitative analysis from the response. 
        Report the response in JSON format with keys company_name, claims, theoretical_analysis and quantitative_analysis.
        """),
        HumanMessage(content=transcript)
    ]
    response = chat(messages)
    formatted_output = eval(response.content)
    company_names = formatted_output["company_name"]
    claims = formatted_output["claims"]

    return company_names, claims


@router.post("/transcribe/breakdown")
def breakdown(request: TranscribeRequest):
    mongo_client = MongoClient()
    video_url = request.video_url
    transcript_result = transcribe(video_url)

    if transcript_result.lang_code != "en":
        response = """At present, we offer support for finance videos in English,
        with plans to introduce additional language options in the near future."""
        return response
    
    filter = content_filter(transcript_result.title, transcript_result.description)
    if not filter:
        response = """This video is not about finance. Please provide a finance video."""
        return response
    
    stock_names, claims = extract_claims(transcript_result.transcript)

    # Store Transcription and Claims in Mongo DB
    mongo_client = pymongo.MongoClient(mongo_client.mongo_uri)
    db = mongo_client.get_database("local")
    collection = db.get_collection("skeptic")

    breakdown_results = {
            "_id": str(ObjectId()),
            "video_id": transcript_result.video_id, 
            "video_link": video_url,
            "transcript": transcript_result.transcript,
            "claims": claims, 
            "stock_names": stock_names,
        }
    
    collection.insert_one(breakdown_results)

    return breakdown_results



# def store_json(response1, response2):
#     """
#     Writes two JSON files for Claims and Thesis
#     :param username: YouTube video author
#     :param response1: claims
#     :param response2: thesis
#     """

#     with open(f'app/database/claims.json', 'w', encoding='utf-8') as f:
#         json.dump(response1, f, ensure_ascii=False, indent=4)

#     with open(f'app/database/thesis.json', 'w', encoding='utf-8') as f:
#         json.dump(response2, f, ensure_ascii=False, indent=4)

# claims, thesis = {}, {"thesis_theoretical": [], "thesis_quantitative": []}
# claims[formatted_output["company_name"]] = formatted_output["claims"]

# for i, text in enumerate(formatted_output["theoretical_analysis"]):
#     thesis["thesis_theoretical"].append({f"Thesis{i}": text})

# for i, text in enumerate(formatted_output["quantitative_analysis"]):
#     thesis["thesis_quantitative"].append({f"Thesis{i}": text})
