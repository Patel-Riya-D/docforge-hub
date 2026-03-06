from notion_client import Client
import os
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
print("DATABASE ID:", NOTION_DATABASE_ID)
notion = Client(auth=NOTION_TOKEN)

def convert_table(headers, rows):

    table_rows = []

    table_rows.append({
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

    blocks = []

    for section in sections:

        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {"type": "text", "text": {"content": section["name"]}}
                ]
            }
        })

        for block in section["blocks"]:

            # Paragraph
            if block["type"] == "paragraph":
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": block["content"]}
                            }
                        ]
                    }
                })

            # Bullet list
            elif block["type"] in ["bullet", "bulleted_list_item"]:
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
            elif block["type"] == "image":
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
            elif block["type"] == "table":

                rows = []

                for row in block["rows"]:
                    cells = []

                    for cell in row:
                        cells.append([{
                            "type": "text",
                            "text": {"content": str(cell)}
                        }])

                    rows.append({
                        "type": "table_row",
                        "table_row": {"cells": cells}
                    })

                blocks.append({
                    "object": "block",
                    "type": "table",
                    "table": {
                        "table_width": len(block["rows"][0]),
                        "has_column_header": True,
                        "has_row_header": False,
                        "children": rows
                    }
                })
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