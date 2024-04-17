import ast
from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from app.utils.output_parsers import parsers
from app.config.models import GPT4Config, ThesisResponse
from app.config.logs import MyLogger
from langchain_core.output_parsers import JsonOutputParser


my_logger = MyLogger()
logger = my_logger.get_logger()


def content_filter(title, description):
    """
    title: YouTube Video Title
    description: YouTube Video Description
    return: bool (True or False)
    """
    openai_config = GPT4Config()
    chat = ChatOpenAI(
        temperature=openai_config.temperature,
        model_name=openai_config.model_name,
        max_tokens=3,
        request_timeout=openai_config.timeout,
    )

    template = """
        You are a honest assistant. 
        You are provided with Youtube video title and description.
        Your task is to classify whether the title and description are related to any of the topics listed below
        [Finance, Financial Education, Financial Advice, Stock Markets, Stock Recommendation].
        Response should be strictly limited to either YES or NO. Do not include anything else in the response.
        """
    system_message_prompt = SystemMessagePromptTemplate.from_template(template)
    human_template = "{title}, {description}"
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message_prompt, human_message_prompt]
    )
    prompt = chat_prompt.format_prompt(
        title=title, description=description
    ).to_messages()
    response = chat(prompt)
    parsed_response = parsers(response.content, dtype="boolean")
    logger.debug(f"Parsed Response - {parsed_response}")
    return parsed_response


def extract_claims_and_thesis(transcript):
    """
    Takes YouTube transcript as input, extracts stock name, claims, theoretical and quantitative thesis
    :param transcript:
    :return: writes JSON files for theoretical and quantitative parts
    """
    parser = JsonOutputParser(pydantic_object=ThesisResponse)

    openai_config = GPT4Config()
    chat = ChatOpenAI(
        temperature=openai_config.temperature,
        model_name=openai_config.model_name,
        max_tokens=openai_config.max_tokens,
        request_timeout=openai_config.timeout,
    )

    template = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(
                """
                You are a respectful, honest, truthful and helpful Financial Analyst. 
                You are provided with a youtube video transcript of a Financial Influencer. 
                Your first task is to identify and extract unique company names in the transcript.
                If no company names are found, return response as None.
                Second task is to extract claims made by the Financial Influencer in list format.
                Third task is to generate theoretical thesis for each claim in list format.
                Report the response in JSON format with keys stock_names, claims, theoretical_analysis.
                """
            ),
            HumanMessagePromptTemplate.from_template(f"{transcript}"),
        ]
    )

    messages = template.format_prompt(format_instructions=parser.get_format_instructions()).to_messages()
    response = chat(messages)
    parsed_output = parser.invoke(response)
    logger.info(f"Claims Extract LLM response - {parsed_output}")
    return parsed_output


def extract_whole_truth(risk_profile: str, thesis: str) -> str:
    openai_config = GPT4Config()
    chat = ChatOpenAI(
        temperature=openai_config.temperature,
        model_name=openai_config.model_name,
        max_tokens=128,
        request_timeout=openai_config.timeout,
    )

    template = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(
                """
            You are a dedicated, honest, helpful and truthful Financial Advisor.
            Your task is to provide reliable guidance to individuals combating misinformation regarding financial matters.
            You are responding to an individual who is watching a YouTube video featuring a Financial Influencer.
            You will be provided with a segment of the video transcript where the Financial Influencer presents an investment thesis.
            Your task is to present a counter-thesis succinctly to the individual based on his risk profile - {risk_profile}.
            Consider that the individual is not well-versed in finance and may not be familiar with financial terminology.
            Do not include any extraneous information or disclaimers beyond the core counter-analysis.
            Avoid directly stating phrases similar to the following:
            "It's advisable to consult with a financial advisor to ensure your investment decisions align with your financial goals and risk tolerance."
            People trust your expertise as a Financial Advisor. Be mindful not to repeat similar text in your response.
            """
            ),
            HumanMessagePromptTemplate.from_template("{text}"),
        ]
    )

    response = chat(template.format_messages(text=thesis, risk_profile=risk_profile))
    logger.info(f"Whole truth LLM response - {response.content}")
    return response.content
