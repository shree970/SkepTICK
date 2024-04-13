from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.utils.prompt_helper import extract_whole_truth
from app.utils.crud import MongoDB
from app.config.logs import MyLogger


router = APIRouter()
my_logger = MyLogger()
logger = my_logger.get_logger()
mongo = MongoDB()


@router.post("/whole_truth")
async def whole_truth(video_id: str, risk_profile: str) -> JSONResponse:
    """
    check for video_id, and Risk_profile, and return wholeTruth
    :param video_id:
    :param risk_profile:
    :return:
    """

    try:
        fetch_db = mongo.read({"video_id": video_id})
        logger.info(f"Fetched the video metadata from MongoDB: {fetch_db.get('video_id')}")
        if fetch_db.get("whole_truth") and fetch_db.get("whole_truth").get(risk_profile):
            response = {"video_id": video_id, "whole_truth": fetch_db.get("whole_truth")[risk_profile]}
            return JSONResponse(content=response, status_code=200)

        counter_analysis = []
        for thesis in fetch_db["thesis"]:
            analysis = extract_whole_truth(risk_profile, thesis)
            counter_analysis.append(analysis)

        if fetch_db.get("whole_truth"):
            fetch_db["whole_truth"][risk_profile] = counter_analysis
            mongo.update(query={"video_id": video_id}, new_data=fetch_db)
        else:
            output = {f"{risk_profile}": counter_analysis}
            new_field = {"whole_truth": output}
            mongo.update(query={"video_id": video_id}, new_data=new_field)

        response = {"video_id": video_id, "whole_truth": counter_analysis}
        return JSONResponse(content=response, status_code=200)

    except Exception as exp:
        logger.error(f"An error occurred: {exp}")
        raise HTTPException(status_code=500, detail=str(exp))
