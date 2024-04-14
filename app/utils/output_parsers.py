from langchain.output_parsers.boolean import BooleanOutputParser


def parsers(text: str, dtype: str) -> str:
    parsed_output = ""
    if dtype == "boolean":
        obj = BooleanOutputParser()
        parsed_output = obj.parse(text)
    return parsed_output
