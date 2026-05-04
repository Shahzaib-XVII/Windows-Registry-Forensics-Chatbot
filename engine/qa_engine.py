import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from groq import Groq
from dotenv import load_dotenv
from indexer.embedder import search
from indexer.db import get_connection

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def get_full_record(db_id, record_type):
    """
    Fetches the full record from SQLite by ID.
    """
    conn = get_connection()
    cursor = conn.cursor()

    if record_type == "event":
        cursor.execute("""
            SELECT * FROM events WHERE id = ?
        """, (db_id,))
    else:
        cursor.execute("""
            SELECT * FROM registry_entries WHERE id = ?
        """, (db_id,))

    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def format_evidence(results):
    """
    Formats ChromaDB search results into readable evidence blocks.
    """
    evidence_blocks = []
    references = []

    for i, (doc, meta) in enumerate(zip(
        results['documents'][0],
        results['metadatas'][0]
    )):
        ref_id = f"[REF-{i+1}]"

        if meta['type'] == 'event':
            block = (
                f"{ref_id} WINDOWS EVENT LOG\n"
                f"  EventID   : {meta['event_id']}\n"
                f"  Timestamp : {meta['timestamp']}\n"
                f"  Source    : {meta['source']}\n"
                f"  Computer  : {meta['computer']}\n"
                f"  Level     : {meta['level']}\n"
                f"  Message   : {doc[doc.find('Message'):doc.find('Time')].replace('Message ', '').strip()}\n"
                f"  Log File  : {meta['file_source']}"
            )
        else:
            block = (
                f"{ref_id} WINDOWS REGISTRY\n"
                f"  Hive      : {meta['hive']}\n"
                f"  Key Path  : {meta['key_path']}\n"
                f"  Value     : {meta['value_name']}\n"
                f"  Data      : {meta['value_data'][:150]}\n"
                f"  Hive File : {meta['file_source']}"
            )

        evidence_blocks.append(block)
        references.append({
            "ref_id": ref_id,
            "type": meta['type'],
            "db_id": meta['db_id'],
            "meta": meta
        })

    return "\n\n".join(evidence_blocks), references


def ask(question, n_results=5):
    """
    Main function — takes a question and returns an AI answer with evidence.
    """
    print(f"\n[QA] Question: {question}")
    print(f"[QA] Searching evidence...")

    # Step 1 — Search ChromaDB for relevant records
    results = search(question, n_results=n_results)

    if not results['documents'][0]:
        return {
            "question": question,
            "answer": "No relevant evidence found in the loaded logs.",
            "references": [],
            "evidence_text": ""
        }

    # Step 2 — Format evidence
    evidence_text, references = format_evidence(results)

    # Step 3 — Build prompt
    system_prompt = """You are a digital forensics AI assistant helping investigators analyze Windows systems.

You will be given a question from an investigator and a set of evidence extracted from Windows Event Logs and Registry hives.

Your job is to:
1. Answer the question clearly and directly based ONLY on the provided evidence
2. Reference specific evidence using the [REF-N] tags provided
3. State the EventID or Registry key that supports your answer
4. If the evidence does not contain enough information to answer, say so clearly
5. Keep your answer professional and forensically accurate
6. Always mention timestamps when available as they are critical in forensics

Do not make assumptions beyond what the evidence shows."""

    user_prompt = f"""INVESTIGATOR QUESTION:
{question}

EVIDENCE FROM SYSTEM LOGS AND REGISTRY:
{evidence_text}

Please analyze this evidence and answer the investigator's question."""

    print(f"[QA] Sending to Groq API...")

    # Step 4 — Call Groq API
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1024
        )
        answer = response.choices[0].message.content

    except Exception as e:
        answer = f"Error calling Groq API: {str(e)}"

    print(f"[QA] Answer received.")

    return {
        "question": question,
        "answer": answer,
        "references": references,
        "evidence_text": evidence_text
    }


if __name__ == "__main__":
    print("=" * 60)
    print("  FORENSICS Q&A ENGINE — TEST MODE")
    print("=" * 60)

    test_questions = [
        "What programs are set to run at startup?",
        "Were there any system service changes?",
        "What was the last user logged into this system?",
        "Were there any errors or critical events?",
    ]

    for question in test_questions:
        result = ask(question)
        print(f"\n{'='*60}")
        print(f"Q: {result['question']}")
        print(f"\nA: {result['answer']}")
        print(f"\nEVIDENCE REFERENCES:")
        for ref in result['references']:
            print(f"  {ref['ref_id']} → {ref['type'].upper()} | DB ID: {ref['db_id']}")
        print("=" * 60)