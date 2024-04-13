from app.utils.crud import MongoDB
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from bson.objectid import ObjectId
from pytube import extract
from app.utils.helper import transcribe
from app.utils.prompt_helper import content_filter, extract_claims_and_thesis
from app.config.logs import MyLogger

router = APIRouter()
my_logger = MyLogger()
logger = my_logger.get_logger()
mongo = MongoDB()


@router.post("/video_id")
async def get_video_id(video_url: str) -> JSONResponse:
    """
    Checks if the Video URL is already in MongoDB
    if_yes - return {video_id,"isFinancial":bool,"isEnglish":bool}
    if_no - /ValidityTest
    :param video_url: str = YouTube Video URL
    :return: video_id
    """
    try:
        video_id = extract.video_id(video_url)
        logger.info(f"Video ID : {video_id}")

        check_db = mongo.read(query={"video_id": video_id})
        logger.info(f"Mongo DB response: {check_db}")
        if check_db is not None:
            response = {
                "video_id": video_id,
                "isFinancial": check_db.get("isFinancial", False),
                "isEnglish": check_db.get("isEnglish", False)
            }
            return JSONResponse(content=response, status_code=200)
        else:
            response = await validate_url(video_url=video_url)
            return response
    except Exception as exp:
        logger.error(f"An error occurred: {exp}")
        raise HTTPException(status_code=500, detail=str(exp))


@router.post("/ValidityTest")
async def validate_url(video_url: str) -> JSONResponse:
    """
    Extracts Title, Description, Transcript
    Checks validity and gets results for isEnglish, isFinance from DB,
    if both are true with transcript
    Stores in mongo
    :param video_url: str
    :return: JSONResponse
    """
    try:
        transcribe_response = transcribe(video_url)
        logger.info(f"Video Title: {transcribe_response.title}")
        logger.info(f"Video Description: {transcribe_response.description}")
        output = content_filter(transcribe_response.title, transcribe_response.description)

        if transcribe_response.lang_code != "en":
            response = {"video_id": transcribe_response.video_id, "isEnglish": False}
            return JSONResponse(content=response, status_code=200)

        elif not output:
            response = {"video_id": transcribe_response.video_id, "isEnglish": True, "isFinancial": output}
            return JSONResponse(content=response, status_code=200)

        else:
            store_in_db = {
                "_id": ObjectId(),
                "video_url": video_url,
                "video_id": transcribe_response.video_id,
                "isEnglish": True,
                "isFinancial": output,
                "title": transcribe_response.title,
                "description": transcribe_response.description,
                "transcript": transcribe_response.transcript
            }
            mongo.create(store_in_db)
            response = {"video_id": transcribe_response.video_id, "isEnglish": True, "isFinancial": output}
            return JSONResponse(content=response, status_code=200)
    except Exception as exp:
        logger.error(f"An error occurred: {exp}")
        raise HTTPException(status_code=500, detail=str(exp))


@router.post("/transcribe/breakdown")
async def breakdown(video_id: str) -> JSONResponse:
    """
    Extracts claims, thesis and stock names for the Video
    :param video_id: str = YouTube Video ID
    :return: video_id, thesis, stock_names
    """
    try:
        query = {"video_id": video_id}
        fetch_document = mongo.read(query=query)
        logger.info(f"Fetched the video metadata from MongoDB: {fetch_document}")
        output = extract_claims_and_thesis(fetch_document.get("transcript"))

        extract_response = {
            "stock_names": output["stock_names"],
            "claims": output["claims"],
            "thesis": output["theoretical_analysis"],
        }
        mongo.update(query=query, new_data=extract_response)

        response = {
            "video_id": video_id,
            "thesis": extract_response["thesis"],
            "stock_names": extract_response["stock_names"]
        }
        return JSONResponse(content=response, status_code=200)

    except Exception as exp:
        logger.error(f"An error occurred: {exp}")
        raise HTTPException(status_code=500, detail=str(exp))
