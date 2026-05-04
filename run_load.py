import sys
import os
import warnings
import logging

warnings.filterwarnings("ignore")
logging.disable(logging.CRITICAL)
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

sys.path.append(os.path.dirname(__file__))

if __name__ == "__main__":
    mode = sys.argv[1]
    files = sys.argv[2:]
    total = 0

    if mode == "evtx":
        from parser.evtx_parser import parse_evtx_file
        from indexer.embedder import embed_events
        for f in files:
            count = parse_evtx_file(f)
            total += count if count else 0
        embed_events()
        print(f"Loaded {len(files)} event log file(s) - {total} records parsed and indexed.")

    elif mode == "registry":
        from parser.registry_parser import parse_registry_hive 
        from indexer.embedder import embed_registry
        for f in files:
            count = parse_registry_hive(f)
            total += count if count else 0
        embed_registry()
        print(f"Loaded {len(files)} registry hive(s) - {total} entries parsed and indexed.")