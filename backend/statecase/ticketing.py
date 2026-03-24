import requests
import os
import hashlib
from backend.utils.logger import get_logger
from dotenv import load_dotenv
load_dotenv()

logger = get_logger("STATECASE-TICKETING")

NOTION_API_KEY = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_TICKET_DATABASE_ID")


def generate_ticket_hash(question: str) -> str:
    return hashlib.md5(question.lower().encode()).hexdigest()


def format_context(question, filters, chunks, confidence, history, sources):

    history_text = "\n".join([
        f"{h['role']}: {h['message']}"
        for h in history[-5:]
    ]) if history else "No history"

    sources_text = "\n".join(sources) if sources else "No sources"

    chunk_text = "\n\n".join([
        f"{c.get('doc_title')} → {c.get('text')[:200]}"
        for c in chunks[:3]
    ])

    return f"""
Question:
{question}

Conversation:
{history_text}

Filters:
Doc Type: {filters.get("doc_type")}
Industry: {filters.get("industry")}
Version: {filters.get("version")}

Confidence:
{confidence}

Sources:
{sources_text}

Retrieved Evidence:
{chunk_text}
"""

def ticket_exists(ticket_id):
    """
    Check if ticket already exists in Notion.
    """

    try:
        url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

        headers = {
            "Authorization": f"Bearer {NOTION_API_KEY}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

        data = {
            "filter": {
                "property": "Ticket ID",
                "rich_text": {
                    "equals": ticket_id
                }
            }
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            results = response.json().get("results", [])
            return len(results) > 0

        return False

    except Exception as e:
        logger.error(f"Ticket exists check failed: {e}")
        return False

def create_ticket(question, context, filters, confidence, history=None, sources=None):
    """
    Create a ticket in Notion with full context.
    """

    try:
        ticket_id = generate_ticket_hash(question)

        # 🔥 CHECK DUPLICATE
        if ticket_exists(ticket_id):
            logger.info("⚠️ Ticket already exists, skipping creation")
            return True

        context_text = format_context(
            question,
            filters,
            context,
            confidence,
            history,
            sources
        )

        url = "https://api.notion.com/v1/pages"

        headers = {
            "Authorization": f"Bearer {NOTION_API_KEY}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

        data = {
            "parent": {"database_id": DATABASE_ID},
            "properties": {
                "Title": {
                    "title": [
                        {"text": {"content": question}}
                    ]
                },
                "Status": {
                    "select": {"name": "Open"}
                },
                "Priority": {
                    "select": {"name": "Medium"}
                },
                "Ticket ID": {
                    "rich_text": [
                        {"text": {"content": ticket_id}}
                    ]
                }
            },
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": f"Context:\n{context_text}"
                                }
                            }
                        ]
                    }
                }
            ]
        }

        response = requests.post(url, headers=headers, json=data)
        print("NOTION RESPONSE:", response.status_code, response.text)

        if response.status_code == 200:
            logger.info("✅ Ticket created in Notion")
            return True
        else:
            logger.error(f"❌ Notion error: {response.text}")
            return False


    except Exception as e:
        logger.error(f"Ticket creation failed: {e}")
        return False
