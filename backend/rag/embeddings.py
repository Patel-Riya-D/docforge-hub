from langchain_openai import AzureOpenAIEmbeddings
import os
from dotenv import load_dotenv

load_dotenv()


def get_embedding_model():

    return AzureOpenAIEmbeddings(
        azure_deployment=os.getenv("AZURE_EMB_DEPLOYMENT"),
        azure_endpoint=os.getenv("AZURE_EMB_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_EMB_KEY"),
        openai_api_version=os.getenv("AZURE_EMB_API_VERSION")
    )