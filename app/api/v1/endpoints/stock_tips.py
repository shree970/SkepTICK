"""
1. Check for any stock names in DB, else no stock mentioned
2. For the stock mentioned, fetch news articles from web
3. Create summary of the news articles
4. Output format
    {
        "stock_name": str,
        "stock_info": str,
        "news_summary": str,
        "news_articles": list[str]
    }

5. Store the output in MongoDB


"""

import json
import os.path
from pathlib import Path

import matplotlib.pyplot as plt
from dotenv import load_dotenv
from fastapi import APIRouter
from langchain import PromptTemplate
from langchain.callbacks.streaming_stdout_final_only import \
    FinalStreamingStdOutCallbackHandler
from langchain_community.llms import OpenAI
from pydantic import BaseModel

from app.agents.agent import ActionAgent
from app.utils.helper import financial_advisor

load_dotenv()
router = APIRouter()


class TipsRequest(BaseModel):
    username: str


def fetch_db(username):
    with open(f'app/database/claims.json', 'r', encoding='utf-8') as f:
        claims = json.load(f)
    company_name = list(claims.keys())
    return company_name[0]


def create_graph(history, company_name):
    hist_selected = history[['Open', 'Close']]

    plt.switch_backend('Agg')
    hist_selected.plot(kind='line')
    plt.title(f"{company_name} Stock Price")
    plt.xlabel("Date")
    plt.ylabel("Stock Price")

    directory = os.path.join(
        Path(__file__).parent.parent.parent.parent.parent, "chrome-plugin/images")
    image_name = directory + "/image1.png"
    plt.savefig(image_name)
    return "image1.png"


@router.get("/stock_facts")
def stock_tips():
    company_name = "Gujarat Themis Biosyn Ltd"  # fetch_db("Rahul Jain")
    # role of agent is to get investment thesis based on factual data from news source, stock history, balance sheets

    llm = OpenAI(temperature=0, streaming=True, callbacks=[
                 FinalStreamingStdOutCallbackHandler()], verbose=True)
    action_agent = ActionAgent(llm)

    prompt_template = PromptTemplate.from_template(
        "Goal 1) Given the company name {company_name}, get news articles about the company using Company news tool"
        "Goal 2) Get the ticker or trading symbol for {company_name}"
        "Goal 3) Once you have ticker symbol, get the stock history for the company using Stock history tool"
        "Goal 4) Use the same ticker symbol, to get stock analysis for the company using Stock analysis tool"
    )

    prompt = prompt_template.format(company_name=company_name)

    investment_thesis = action_agent.run(prompt)
    print("OUTPUT FROM AGENT", investment_thesis)

    history = financial_advisor(company_name)
    stock_chart = create_graph(history, company_name)
    return stock_chart, investment_thesis
