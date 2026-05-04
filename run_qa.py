import sys
import json
import os
import warnings
import logging

# Suppress ALL warnings and logs before importing anything
warnings.filterwarnings("ignore")
logging.disable(logging.CRITICAL)
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

sys.path.append(os.path.dirname(__file__))

from engine.qa_engine import ask

if __name__ == "__main__":
    question = " ".join(sys.argv[1:])
    result = ask(question)

    clean_refs = []
    for ref in result.get("references", []):
        clean_refs.append({
            "ref_id": ref["ref_id"],
            "type": ref["type"],
            "db_id": ref["db_id"],
            "meta": {k: str(v) for k, v in ref.get("meta", {}).items()}
        })
    result["references"] = clean_refs
    result.pop("evidence_text", None)

    # Print ONLY the JSON — nothing else
    sys.stdout.write(json.dumps(result) + "\n")
    sys.stdout.flush()