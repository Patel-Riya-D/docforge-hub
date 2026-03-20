"""
RAG Evaluation Module using RAGAS

This module evaluates the performance of the RAG pipeline using predefined datasets.

Responsibilities:
- Load evaluation dataset (questions + ground truth)
- Run RAG pipeline to generate answers
- Compare generated answers with ground truth
- Compute evaluation metrics using RAGAS

Metrics Used:
- Faithfulness: Measures how grounded the answer is in retrieved context
- Answer Relevancy: Measures how relevant the answer is to the question

Key Features:
- End-to-end evaluation of retrieval + generation
- Uses real pipeline (not mocked responses)
- Supports batch evaluation

Used by:
- API endpoint: /documents/rag-evaluate
"""
import json
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy,context_precision,context_recall
from backend.rag.query_search_engine import answer_question
from langchain_openai import OpenAIEmbeddings
from openai import OpenAI
import os
from dotenv import load_dotenv
from datetime import datetime

config = {
    "top_k": 3,
    "model": "azure-openai",
    "embedding_model": "text-embedding-3-large",
    "filters": None
}

load_dotenv()

openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large",
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

def run_evaluation():
    """
    Execute RAG evaluation using RAGAS metrics.

    Workflow:
    1. Load evaluation dataset from JSON file
        - Each entry contains:
            question
            ground_truth

    2. For each question:
        - Run RAG pipeline (answer_question)
        - Collect:
            - Generated answer
            - Retrieved context chunks

    3. Construct evaluation dataset:
        - question
        - answer
        - contexts (list of retrieved texts)
        - ground_truth

    4. Run RAGAS evaluation:
        - Compute faithfulness and answer relevancy

    5. Return results as pandas DataFrame

    Returns:
        pandas.DataFrame:
            Contains evaluation scores for each query and overall metrics

    Notes:
    - Uses actual RAG pipeline (not synthetic evaluation)
    - Embeddings are required for RAGAS evaluation
    - Helps assess both retrieval and generation quality
    """

    # ---------------- LOAD DATASET ----------------
    """
    Load evaluation dataset containing:
    - question: user query
    - ground_truth: expected correct answer

    Used to compare RAG output against known answers.
    """
    with open("backend/rag/eval_dataset.json") as f:
        data = json.load(f)

    questions = []
    answers = []
    contexts = []
    ground_truths = []
    results_data = []

    # ---------------- RUN RAG ----------------
    """
    Run full RAG pipeline for each question:
    - Generate answer
    - Retrieve context
    - Store results for evaluation
    """

    for item in data:

        question = item["question"]
        gt = item["ground_truth"]

        if not gt or gt.lower() == "not available":
            print(f"⚠️ Skipping invalid ground truth for: {question}")
            continue

        result = answer_question(question)

        if not result or "chunks" not in result:
            print(f"⚠️ No chunks retrieved for: {question}")
            continue

        answer = result.get("answer", "")
        retrieved_chunks = result.get("chunks", [])

        context_texts = [c.get("text", "") for c in retrieved_chunks if c.get("text")]

        if not context_texts:
            print(f"⚠️ Empty context for: {question}")
            continue

        questions.append(question)
        answers.append(answer)
        contexts.append(context_texts)
        ground_truths.append(gt)

        results_data.append({
            "question": question,
            "answer": answer,
            "contexts": context_texts
        })

    if not questions:
        raise ValueError("❌ No valid evaluation data generated")

    # ---------------- CREATE DATASET ----------------
    dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths
    })

    metrics = [
        faithfulness, 
        answer_relevancy,
        context_precision,
        context_recall
    ]

    result = evaluate(
        dataset=dataset,
        metrics=metrics,
        embeddings=embeddings
    )

    print("\n📊 RAGAS RESULTS:")
    eval_df = result.to_pandas()

    print("Evaluation completed")

    return eval_df

if __name__ == "__main__":
    run_evaluation()