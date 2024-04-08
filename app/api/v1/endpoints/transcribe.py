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
from app.utils.crud import MongoDB
from functools import lru_cache
from typing import Any
from fastapi import APIRouter, HTTPException
from bson.objectid import ObjectId
from app.utils.helper import transcribe
from app.config.models import TranscribeRequest, TranscribeResponse
from app.utils.prompt_helper import content_filter, extract_claims_and_thesis
from app.config.logs import MyLogger

router = APIRouter()
my_logger = MyLogger()
logger = my_logger.get_logger()
mongo = MongoDB()


@lru_cache(maxsize=1)
def cached_transcribe(video_url):
    return transcribe(video_url)


@router.post("/video_id/")
async def get_video_id(request: TranscribeRequest):
    try:
        transcript_result = cached_transcribe(request.video_url)
        if transcript_result.video_id is not None:
            return transcript_result.video_id
        else:
            raise HTTPException(status_code=404, detail="Video ID not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ValidityTest")
async def validate_url(request: TranscribeRequest):
    transcript_result = cached_transcribe(request.video_url)
    logger.info(f"Video Title: {transcript_result.title}")
    logger.info(f"Video Description: {transcript_result.description}")

    if transcript_result.lang_code != "en":
        response = """At present, we offer support for finance videos in English,
        with plans to introduce additional language options in the near future."""
        return response

    output = content_filter(transcript_result.title, transcript_result.description)
    if not output:
        response = """This video is not about finance. Please provide a finance video."""
        return response
    return transcript_result


@router.post("/transcribe/index")
async def check_db(video_id: str):
    logger.info(f"Video ID : {video_id}")
    response = mongo.read(query={"video_id": video_id})
    logger.info(f"Mongo DB response: {response}")

    if response:
        return response
    else:
        return HTTPException(status_code=404, detail="Video not found in the database")


@router.post("/transcribe/breakdown")
async def breakdown(transcript: TranscribeResponse) -> dict[str, Any]:
    response = extract_claims_and_thesis(transcript.transcript)

    breakdown_results = {
        "_id": str(ObjectId()),
        "video_id": transcript.video_id,
        "transcript": transcript.transcript,
        "stock_names": response["stock_names"],
        "claims": response["claims"],
        "thesis": response["theoretical_analysis"],
    }
    mongo.create(breakdown_results)

    return breakdown_results
