"""
TODO:
1. Reading from mongoDB, videoTranscription
2. Add output parser, verify the outputs
3. Add the output to the database
    whole truth : dict['claim': str, 'counter_analysis': str]

"""

from fastapi import APIRouter
from app.utils.prompt_helper import extract_whole_truth
from app.utils.crud import MongoDB
from app.config.logs import MyLogger


router = APIRouter()
my_logger = MyLogger()
logger = my_logger.get_logger()
mongo = MongoDB()


@router.post("/whole_truth")
async def whole_truth(age: int, risk_profile: str, video_id: str) -> list[str]:
    
    # remove sqare brackets in response
    # add exception
    response = mongo.read({"video_id": video_id})
    # check for video_id, and Risk_profile, and return wholeTruth
    # add video ID in response
    
    counter_analysis = []
    for thesis in response["thesis"]:
        analysis = extract_whole_truth(age, risk_profile, thesis)
        counter_analysis.append(analysis)

    new_field = {"whole_truth": counter_analysis}
    mongo.update(query={"video_id": video_id}, new_data=new_field)

    return counter_analysis
