"""
Notion Data Reader Module

This module provides utility functions to fetch data from Notion.

Responsibilities:
- Connect to Notion API using authentication token
- Fetch all pages from a database
- Retrieve block-level content for each page

Used by:
- ingestion module for building RAG dataset
"""
from notion_client import Client
import os
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

notion = Client(auth=NOTION_TOKEN)


def fetch_all_pages():
    """
    Fetch all pages from the configured Notion database.

    Handles pagination internally using Notion API cursors.

    Returns:
        list[dict]: List of Notion page objects

    Notes:
    - Automatically iterates through all pages
    - Uses NOTION_DATABASE_ID from environment variables
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
    """
    Fetch all content blocks for a given Notion page.

    Args:
        page_id (str): Notion page ID

    Returns:
        list[dict]: List of block objects (paragraphs, headings, etc.)

    Notes:
    - Used to extract detailed content from each page
    - Supports parsing of headings, paragraphs, and lists
    """

    response = notion.blocks.children.list(
        block_id=page_id
    )

    return response["results"]