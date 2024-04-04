from langchain.output_parsers.boolean import BooleanOutputParser
from langchain.output_parsers import CommaSeparatedListOutputParser
from langchain.output_parsers import StructuredOutputParser, ResponseSchema


def parsers(text: str, dtype: str) -> str:
    parsed_output = ""
    if dtype == "boolean":
        obj = BooleanOutputParser()
        parsed_output = obj.parse(text)
    if dtype == "list":
        obj = CommaSeparatedListOutputParser()
        parsed_output = obj.parse(text)
    if dtype in ["json", "dict"]:
        obj = StructuredOutputParser()
        response_schemas = [
            ResponseSchema(name="answer", description="answer to the user's question"),
            ResponseSchema(
                name="source",
                description="source used to answer the user's question, should be a website.",
            ),
        ]
        output_parser = obj.from_response_schemas(response_schemas)
        parsed_output = obj.parse(text)
    return parsed_output
