"""
TODO:
1. Reading from mongoDB, videoTranscription
2. Add output parser, verify the outputs
3. Add the output to the database
    whole truth : dict['claim': str, 'counter_analysis': str]

"""

from fastapi import APIRouter
from app.utils.prompt_helper import extract_whole_truth
from app.utils.helper import mongo_client

router = APIRouter()


@router.post("/whole_truth")
async def whole_truth(age: int, risk_profile: str, video_id: str) -> list[str]:
    collection = mongo_client()
    response = collection.find_one({"video_id": video_id})

    counter_analysis = []
    for thesis in response["thesis"]:
        analysis = extract_whole_truth(age, risk_profile, thesis)
        counter_analysis.append(analysis)

    new_field = {"$set": {"whole_truth": counter_analysis}}
    collection.update_one({"video_id": video_id}, new_field)

    return counter_analysis
