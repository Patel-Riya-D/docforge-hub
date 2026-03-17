import json
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from ragas.metrics import ContextRecall
from backend.rag.query_search_engine import answer_question
from ragas.llms import llm_factory
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()

openai_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

def run_evaluation():

    # ---------------- LOAD DATASET ----------------
    with open("backend/rag/eval_dataset.json") as f:
        data = json.load(f)

    questions = []
    answers = []
    contexts = []
    ground_truths = []

    # ---------------- RUN RAG ----------------
    for item in data:

        question = item["question"]
        gt = item["ground_truth"]

        result = answer_question(question)

        answer = result["answer"]
        retrieved_chunks = result["chunks"]

        context_texts = [c["text"] for c in retrieved_chunks]

        questions.append(question)
        answers.append(answer)
        contexts.append(context_texts)
        ground_truths.append(gt)

    # ---------------- CREATE DATASET ----------------
    dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths
    })

    # ragas LLM
    ragas_llm = llm_factory(
        "gpt-4o-mini",
        client=openai_client
    )

    metrics = [
        faithfulness, answer_relevancy]

    result = evaluate(
        dataset=dataset,
        metrics=metrics
    )

    print("\n📊 RAGAS RESULTS:")
    print(result.to_pandas())


if __name__ == "__main__":
    run_evaluation()