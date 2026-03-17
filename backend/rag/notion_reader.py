from notion_client import Client
import os
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

notion = Client(auth=NOTION_TOKEN)


def fetch_all_pages():
    """
    Fetch all pages from the database.
    """
    results = []
    cursor = None

    while True:
        response = notion.databases.query(
            database_id=DATABASE_ID,
            start_cursor=cursor
        )
        results.extend(response["results"])

        if not response.get("has_more"):
            break

        cursor = response["next_cursor"]

    return results


def fetch_page_blocks(page_id):

    response = notion.blocks.children.list(
        block_id=page_id
    )

    return response["results"]