import requests
import os
import hashlib
from backend.utils.logger import get_logger
from backend.statecase.ticket_utils import classify_ticket
from backend.utils.redis_client import redis_client
from dotenv import load_dotenv
load_dotenv()

logger = get_logger("STATECASE-TICKETING")

NOTION_API_KEY = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_TICKET_DATABASE_ID")


def generate_ticket_hash(question: str) -> str:
    return hashlib.md5(question.lower().encode()).hexdigest()

def set_ticket_status(ticket_id, status):
    redis_client.set(f"ticket_status:{ticket_id}", status)


def get_ticket_status(ticket_id):
    return redis_client.get(f"ticket_status:{ticket_id}")


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

def update_ticket_status(ticket_id, status):
    """
    Update ticket status in Notion.
    """

    valid_status = ["Open", "In Progress", "Closed"]

    if status not in valid_status:
        return {
            "success": False,
            "error": f"Invalid status: {status}"
        }

    try:
        # 🔍 Step 1: Find ticket by Ticket ID
        query_url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

        headers = {
            "Authorization": f"Bearer {NOTION_API_KEY}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

        query_data = {
            "filter": {
                "property": "Ticket ID",
                "rich_text": {
                    "equals": ticket_id
                }
            }
        }

        response = requests.post(query_url, headers=headers, json=query_data)

        if response.status_code != 200:
            logger.error(f"❌ Query failed: {response.text}")
            return False

        results = response.json().get("results", [])

        if not results:
            logger.warning("⚠️ Ticket not found")
            return False

        page_id = results[0]["id"]

        # 🔄 Step 2: Update status
        update_url = f"https://api.notion.com/v1/pages/{page_id}"

        update_data = {
            "properties": {
                "Status": {
                    "select": {"name": status}
                }
            }
        }

        update_response = requests.patch(update_url, headers=headers, json=update_data)

        if update_response.status_code == 200:
            logger.info(f"✅ Ticket updated to {status}")
            return {
                "success": True,
                "ticket_id": ticket_id,
                "status": status
            }
        else:
            logger.error(f"❌ Update failed: {update_response.text}")
            return {
                "success": False,
                "error": update_response.text
            }

    except Exception as e:
        logger.error(f"Update ticket failed: {e}")
        return False

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

def create_ticket(question, context, filters, confidence, history=None, sources=None, user_id="default_user"):
    """
    Create a ticket in Notion with full context.
    """

    try:

        # 🔥 classify ticket using AI
        ticket_meta = classify_ticket(question)

        category = ticket_meta["category"]
        owner = ticket_meta["owner"]
        priority = ticket_meta["priority"]

        print("TICKET META:", ticket_meta)

        #  CHECK DUPLICATE
        ticket_id = generate_ticket_hash(question)

        # ✅ check FIRST
        if ticket_exists(ticket_id):
            set_ticket_status(ticket_id, "exists")   # 🔥 IMPORTANT
            return "exists", ticket_id

        # then creating
        set_ticket_status(ticket_id, "creating")

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
                    "select": {"name": priority}
                },
                "Owner": {
                    "rich_text": [
                        {"text": {"content": owner}}
                    ]
                },
                "Category": {
                    "select": {"name": category}
                },
                "Ticket ID": {
                    "rich_text": [
                        {"text": {"content": ticket_id}}
                    ]
                },
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
            set_ticket_status(ticket_id, "created")   # ✅ ADD THIS
            logger.info("✅ Ticket created in Notion")
            return "created", ticket_id
        else:
            set_ticket_status(ticket_id, "failed")   # ✅ ADD THIS
            logger.error(f"❌ Notion error: {response.text}")
            return "error", None

    except Exception as e:
        set_ticket_status(ticket_id, "failed")   # ✅ ADD THIS
        logger.error(f"Ticket creation failed: {e}")
        return "error", None
