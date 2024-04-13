from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from app.utils.output_parsers import parsers
from app.config.models import GPT4Config
from app.config.logs import MyLogger


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
        request_timeout=openai_config.timeout
    )

    template = (
        """
        You are a honest assistant. 
        You are provided with Youtube video title and description.
        Your task is to classify whether the title and description are related to any of the topics listed below
        [Finance, Financial Education, Financial Advice, Stock Markets, Stock Recommendation].
        Response should be strictly limited to either YES or NO. Do not include anything else in the response.
        """
    )
    system_message_prompt = SystemMessagePromptTemplate.from_template(template)
    human_template = "{title}, {description}"
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])
    prompt = chat_prompt.format_prompt(title=title, description=description).to_messages()
    logger.debug(f"Content Filter Prompt - {prompt}")
    response = chat(prompt)
    logger.debug(f"Content Filter LLM response - {response}")
    parsed_response = parsers(response.content, dtype="boolean")
    logger.debug(f"Parsed Response - {parsed_response}")
    return parsed_response


def extract_claims_and_thesis(transcript):
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
        You are a honest Financial Analyst. 
        You are provided with a youtube video transcript of a Financial Influencer. 
        Your first task is to identify and extract unique company names in the transcript.
        If no company names are found, return response as None.
        Second task is to extract claims made by the Financial Influencer and generate theoretical thesis for each claim.
        Report the response in JSON format as mentioned below with keys stock_names, claims, theoretical_analysis.
        
        Output format:
        {'stock_names': [], 'claims': ['<claim 1>', '<claim 2>'], 'theoretical_analysis': ['<thesis 1>', '<thesis 2>']}
        """),
        HumanMessage(content=transcript)
    ]
    response = chat(messages)
    logger.info(f"Claims Extract LLM response - {response.content}")
    # parsed_output = parsers(response.content, dtype="dict")
    # logger.info(f"Parsed Response - {parsed_output}")

    return eval(response.content)


def extract_whole_truth(risk_profile: str, thesis: str, ) -> str:
    openai_config = GPT4Config()
    chat = ChatOpenAI(
        temperature=openai_config.temperature,
        model_name=openai_config.model_name,
        request_timeout=openai_config.timeout,
    )

    template = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=("""
            You are a dedicated Financial Advisor.
            Your task is to provide reliable guidance to individuals combating misinformation regarding financial matters.
            You are responding to an individual who is watching a YouTube video featuring a Financial Influencer.
            You will be provided with a segment of the video transcript where the Financial Influencer presents an investment thesis.
            Your role is to present a counter-thesis succinctly to the individual.
            Consider that the individual is not well-versed in finance and may not be familiar with financial terminology.
            Take into account the individual's risk profile.
            Assume that younger individuals tend to be more tolerant of risk, while older individuals tend to be more risk-averse.
            Do not include any extraneous information or disclaimers beyond the core counter-analysis.
            Avoid directly stating phrases similar to the following:
            "It's advisable to consult with a financial advisor to ensure your investment decisions align with your financial goals and risk tolerance."
            People trust your expertise as a Financial Advisor. Be mindful not to repeat similar text in your response.
            Response format:
            [<counter analysis1>, <counter analysis2>, <counter analysis3>]
            """)
                          ),
            HumanMessagePromptTemplate.from_template("{text}, {risk_profile}"),
        ]
    )

    response = chat(template.format_messages(text=thesis, risk_profile=risk_profile))
    logger.info(f"Whole truth LLM response - {response.content}")
    # parsed_output = parsers(response.content, dtype="list")
    # logger.info(f"Parsed Response - {parsed_output}")
    return response.content
