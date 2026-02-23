import os
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv

load_dotenv()

def get_llm():

    return AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_LLM_DEPLOYMENT_41_MINI"),
        api_version=os.getenv("AZURE_LLM_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_LLM_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_LLM_KEY"),
        temperature=0.3,
    )