import os
import requests
import yfinance as yf
from yahooquery import Ticker
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

        return TranscribeResponse(video_id=video_id, lang_code=lang_code, title=title, description=description,
                                  transcript=transcript)
    except NoTranscriptFound:
        return TranscribeResponse(video_id=video_id)


def get_company_news(company_name):
    params = {
        "engine": "google",
        "tbm": "nws",
        "q": company_name,
        "api_key": os.environ["SERPAPI_API_KEY"],
    }

    response = requests.get('https://serpapi.com/search', params=params)
    data = response.json()

    return data.get('news_results')


def write_news_to_file(news, filename):
    with open(filename, 'w') as file:
        for news_item in news:
            if news_item is not None:
                title = news_item.get('title', 'No title')
                link = news_item.get('link', 'No link')
                date = news_item.get('date', 'No date')
                file.write(f"Title: {title}\n")
                file.write(f"Link: {link}\n")
                file.write(f"Date: {date}\n\n")


def get_stock_evolution(company_name, period="1y"):
    # Get the stock information
    stock = yf.Ticker(company_name)

    # Get historical market data
    hist = stock.history(period=period)

    # Convert the DataFrame to a string with a specific format
    data_string = hist.to_string()

    # Append the string to the "investment.txt" file
    with open("../assets/investment.txt", "a") as file:
        file.write(f"\nStock Evolution for {company_name}:\n")
        file.write(data_string)
        file.write("\n")

    return hist


def get_financial_statements(ticker):
    # Create a Ticker object
    company = Ticker(ticker)

    # Get financial data
    balance_sheet = company.balance_sheet().to_string()
    cash_flow = company.cash_flow(trailing=False).to_string()
    income_statement = company.income_statement().to_string()
    valuation_measures = str(company.valuation_measures)  # This one might already be a dictionary or string

    # Write data to file
    with open("../assets/investment.txt", "a") as file:
        file.write("\nBalance Sheet\n")
        file.write(balance_sheet)
        file.write("\nCash Flow\n")
        file.write(cash_flow)
        file.write("\nIncome Statement\n")
        file.write(income_statement)
        file.write("\nValuation Measures\n")
        file.write(valuation_measures)


def get_data(company_name, company_ticker, filename="app/assets/investment.txt"):
    news = get_company_news(company_name)
    if news:
        write_news_to_file(news, filename)
    else:
        print("No news found.")

    hist = get_stock_evolution(company_ticker)
    get_financial_statements(company_ticker)
    return hist


def financial_advisor(request):
    print(f"Received request: {request}")
    hist = get_stock_evolution("GUJTHEM.BO")
    return hist
