"""
notion_publisher.py

This module handles publishing generated documents from DocForge Hub
to Notion using the Notion API.

It converts structured draft content into Notion-compatible blocks,
including:
- Headings (H1, H2)
- Paragraphs
- Bullet lists
- Tables
- Form-style fields
- Images (external only)

Key Features:
- Structured block conversion for Notion API
- Special handling for FORM documents
- Table transformation into Notion table blocks
- Chunked upload to comply with Notion API limits
- Metadata storage (version, type, industry, tags, timestamps)

This module enables seamless integration between DocForge Hub
and Notion-based document workflows.
"""
from notion_client import Client
import os
from dotenv import load_dotenv
from datetime import datetime
import pytz


load_dotenv()

IST = pytz.timezone("Asia/Kolkata")

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
print("DATABASE ID:", NOTION_DATABASE_ID)
notion = Client(auth=NOTION_TOKEN)

def convert_table(headers, rows):
    """
    Convert structured table data into Notion table block format.

    Args:
        headers (list[str]): List of column headers.
        rows (list[list]): Table rows.

    Returns:
        dict: Notion-compatible table block.

    Behavior:
        - Creates header row with column titles
        - Converts each row into Notion table_row blocks
        - Enables column headers

    Notes:
        - Used internally by publish_document_to_notion
        - Ensures consistent table rendering in Notion
    """

    table_rows = []

    table_rows.append({
        "object": "block",
        "type": "table_row",
        "table_row": {
            "cells": [[{"type": "text", "text": {"content": h}}] for h in headers]
        }
    })

    for r in rows:
        table_rows.append({
            "type": "table_row",
            "table_row": {
                "cells": [[{"type": "text", "text": {"content": str(c)}}] for c in r]
            }
        })

    return {
        "object": "block",
        "type": "table",
        "table": {
            "table_width": len(headers),
            "has_column_header": True,
            "has_row_header": False,
            "children": table_rows
        }
    }


def publish_document_to_notion(
    document_name,
    sections,
    version,
    document_type,
    industry,
    tags,
    created_by,
    created_at,
    template_id=None    
):
    """
    Publish a generated document to Notion.

    This function:
    - Converts structured draft sections into Notion blocks
    - Creates a new page in the configured Notion database
    - Uploads content in chunks to comply with API limits

    Args:
        document_name (str): Name of the document.
        sections (list): List of sections with structured blocks.
        version (int): Document version number.
        document_type (str): Type of document (e.g., POLICY, FORM).
        industry (str): Industry classification.
        tags (list[str]): Tags for categorization.
        created_by (str): Creator name.
        created_at (str): ISO timestamp.
        template_id (str, optional): Template reference (unused currently).

    Returns:
        None

    Workflow:
        1. Initialize Notion blocks with document title
        2. Iterate through sections:
            - Add headings and dividers
            - Convert paragraphs, bullets, tables
            - Handle FORM-specific rendering
        3. Normalize timestamp to IST timezone
        4. Create Notion page with metadata
        5. Upload content in chunks (max 100 blocks per request)

    Supported Block Types:
        - paragraph → Notion paragraph
        - bullet → bulleted list item
        - table → Notion table block
        - image → external image block
        - diagram → skipped (Notion limitation)

    Special Handling:
        - FORM documents → rendered as structured fields
        - Table of Contents → simplified (removes page column)
        - Checkbox fields → converted to Notion to-do items

    Notes:
        - Notion does not support local images → diagrams skipped
        - Uses environment variables for authentication
        - Handles API limits via chunking

    Raises:
        Exception: If Notion API call fails (not explicitly handled here).
    """
    blocks = []

    blocks.insert(0,{
        "object":"block",
        "type":"heading_1",
        "heading_1":{
            "rich_text":[{
                "type":"text",
                "text":{"content":document_name}
            }]
        }
    })

    for section in sections:

        if not isinstance(section, dict):
            continue

        blocks.append({
            "object": "block",
            "type": "divider",
            "divider": {}
        })

        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {"type": "text", "text": {"content": section["name"]}}
                ]
            }
        })

        # FORM rendering (table instead of paragraphs)
        if document_type.upper() == "FORM":

            form_rows = []

            for block in section.get("blocks", []):

                if not isinstance(block, dict):
                    continue

                if block.get("type") == "paragraph":

                    text = block.get("content", "").strip()

                    if text.startswith("☐"):

                        blocks.append({
                            "object": "block",
                            "type": "to_do",
                            "to_do": {
                                "rich_text": [{
                                    "type": "text",
                                    "text": {"content": text.replace("☐", "").strip()}
                                }],
                                "checked": False
                            }
                        })

                    else:

                        field = text.split(":")[0].strip()
                        value = text.split(":")[1].strip() if ":" in text else ""

                        form_rows.append([field, value])

            if form_rows:

                for row in form_rows:

                    field = row[0]

                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{
                                "type": "text",
                                "text": {
                                    "content": f"{field}: _______________________"
                                }
                            }]
                        }
                    })

            continue

        for block in section.get("blocks", []):

            if not isinstance(block, dict):

                continue

            # Paragraph
            if block.get("type") == "paragraph":

                text = block.get("content", "")
                lines = [l.strip() for l in text.split("\n") if l.strip()]

                if all(l.startswith(("-", "•")) for l in lines):

                    for line in lines:
                        clean = line.lstrip("-• ").strip()

                        blocks.append({
                            "object": "block",
                            "type": "bulleted_list_item",
                            "bulleted_list_item": {
                                "rich_text": [{
                                    "type": "text",
                                    "text": {"content": clean}
                                }]
                            }
                        })

                else:
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{
                                "type": "text",
                                "text": {"content": text}
                            }]
                        }
                    })
            
            elif block.get("type") == "diagram":
                # Notion cannot display local diagrams
                continue
            
            # Bullet list
            elif block.get("type") in ["bullet", "bulleted_list_item"]:
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": block["content"]}
                            }
                        ]
                    }
                })
            
            # Image
            elif block.get("type") == "image":
                blocks.append({
                    "object": "block",
                    "type": "image",
                    "image": {
                        "type": "external",
                        "external": {
                            "url": block["url"]
                        }
                    }
                })

            # Table
            elif block.get("type") == "table":

                headers = block.get("headers", [])
                rows = block.get("rows", [])

                # Fix Table of Contents (remove Page column)
                if headers == ["Section", "Page"]:

                    headers = ["Section"]
                    rows = [[f"{i+1}. {row[0]}"] for i, row in enumerate(rows)]

                table_block = convert_table(headers, rows)

                blocks.append(table_block)
            
    # Ensure timestamp is IST
    if not created_at:
        created_at = datetime.now(IST).isoformat()
    else:
        try:
            created_at = datetime.fromisoformat(created_at)
            created_at = created_at.astimezone(IST).isoformat()
        except:
            created_at = datetime.now(IST).isoformat()

    page = notion.pages.create(
        parent={"database_id": NOTION_DATABASE_ID},
        properties={
            "Name": {
                "title": [
                    {"text": {"content": document_name}}
                ]
            },
            "Version": {
                "number": version
            },
            "Document Type": {
                "select": {"name": document_type}
            },
            "Industry": {
                "select": {"name": industry}
            },
            "Tags": {
                "multi_select": [{"name": tag} for tag in tags]
            },
            "Created By": {
                "rich_text": [
                    {"text": {"content": created_by}}
                ]
            },
            "Created At": {
                "date": {
                    "start": created_at
                }
            }
        }
    )

    page_id = page["id"]

    MAX_BLOCKS = 100

    for i in range(0, len(blocks), MAX_BLOCKS):

        chunk = blocks[i:i + MAX_BLOCKS]

        notion.blocks.children.append(
            block_id=page_id,
            children=chunk
        )