"""E30: how does our retrieval compare with the usual industry baselines? (mentor question: "have we validated our RAG?")

Same gold set as E17 (14 questions with a gold fact in the real 48-page Federal Council booklet, German). Compared on the standard retrieval metrics
(recall@k, MRR@10, nDCG@10; a chunk is relevant if it contains the gold phrase):
  bm25_shipped   what the app does: sentence-packed chunks of 480 characters, BM25 with accent folding and 6-character stems, ballot-question chunk pinned
  bm25_plain     the same BM25 scores without the pinning (isolates the scorer)
  dense_*        multilingual dense retrieval on CPU (fastembed / ONNX): intfloat/multilingual-e5-large and paraphrase-multilingual-MiniLM-L12-v2
  hybrid_*       reciprocal rank fusion (k = 60) of BM25 and the dense ranking: the common industry default
and three chunk sizes (480, 960, 1 500 characters ≈ 120, 240, 375 tokens; bigger chunks make a gold phrase less likely to be cut, which favours them).
Not tested here: cross-encoder re-ranking, query rewriting / HyDE (no model for them on the endpoints we can use; the LLM could do the rewriting).

    uv venv ragenv && uv pip install --python ragenv/Scripts/python.exe fastembed numpy python-dotenv httpx pydantic
    ragenv/Scripts/python.exe research/exp30_rag_baselines.py            # needs the booklet text (research/download_booklet.py)
"""
import json
import math
import re
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src" / "backend"))
sys.path.insert(0, str(HERE))
from graph.corpus import _tokens, chunk_text, retrieve_passages  # noqa: E402

TEXT = (HERE / "data" / "booklets" / "erlaeuterungen_2025-09-28_de.txt").read_text(encoding="utf-8")
src = (HERE / "exp17_real_booklet.py").read_text(encoding="utf-8")
ns: dict = {}
exec(src[src.index("QA = ["):src.index("UNANSWERABLE")], {"re": re}, ns)  # the 14 (question, gold regex) pairs of E17, unchanged
QA = ns["QA"]
NORM = lambda s: " ".join(s.split())
MODELS = {"e5-large": ("intfloat/multilingual-e5-large", "query: ", "passage: "),
          "minilm": ("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", "", "")}
K_RRF = 60


def bm25_rank(chunks, query):
    docs = [{} for _ in chunks]
    for d, c in zip(docs, chunks):
        for t in _tokens(c["text"]):
            d[t] = d.get(t, 0) + 1
    n = len(chunks)
    avg = sum(sum(d.values()) for d in docs) / n
    df = {}
    for d in docs:
        for t in d:
            df[t] = df.get(t, 0) + 1
    q = set(_tokens(query))
    scores = []
    for d in docs:
        ln = sum(d.values()) or 1
        scores.append(sum(math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5)) * d[t] * 2.5 / (d[t] + 1.5 * (0.25 + 0.75 * ln / avg)) for t in q if t in d))
    return list(np.argsort(-np.array(scores), kind="stable")), scores


def rrf(*rankings):
    s = {}
    for r in rankings:
        for pos, i in enumerate(r):
            s[i] = s.get(i, 0.0) + 1.0 / (K_RRF + pos + 1)
    return sorted(s, key=lambda i: -s[i])


def metrics(ranked_hits):
    """ranked_hits: per question a list of booleans (is the chunk at this rank relevant) over the top 10, plus the total number of relevant chunks."""
    out = {"recall@1": 0.0, "recall@4": 0.0, "recall@6": 0.0, "recall@8": 0.0, "mrr@10": 0.0, "ndcg@10": 0.0}
    for hits in ranked_hits:
        for k in (1, 4, 6, 8):
            out[f"recall@{k}"] += any(hits[:k])
        first = next((i for i, h in enumerate(hits[:10]) if h), None)
        out["mrr@10"] += 1 / (first + 1) if first is not None else 0
        dcg = sum(h / math.log2(i + 2) for i, h in enumerate(hits[:10]))
        ideal = sum(1 / math.log2(i + 2) for i in range(min(10, max(1, sum(hits[:10])))))
        out["ndcg@10"] += dcg / ideal if sum(hits[:10]) else 0
    return {k: round(v / len(ranked_hits), 3) for k, v in out.items()}


def main():
    from fastembed import TextEmbedding

    models = {}
    for name, (mid, qp, pp) in MODELS.items():
        t0 = time.time()
        models[name] = (TextEmbedding(model_name=mid), qp, pp)
        print(f"loaded {mid} in {time.time() - t0:.0f} s", flush=True)
    results = {}
    for size in (480, 960, 1500):
        chunks = [c for c in chunk_text("--- Author notes / pasted text ---\n" + TEXT, "booklet", "de", size=size)]
        texts = [NORM(c["text"]) for c in chunks]
        rel = [[bool(re.search(g, t, re.I)) for t in texts] for _, g in QA]
        emb = {}
        for name, (m, qp, pp) in models.items():
            t0 = time.time()
            emb[name] = np.array(list(m.embed([pp + t for t in texts], batch_size=16)))
            print(f"  size {size}: {len(chunks)} chunks embedded with {name} in {time.time() - t0:.0f} s", flush=True)
        rows = {"bm25_shipped": [], "bm25_pin1": [], "bm25_plain": []}
        for name in models:
            rows[f"dense_{name}"], rows[f"hybrid_{name}"] = [], []
        for qi, (q, g) in enumerate(QA):
            shipped = retrieve_passages(chunks, q, top_k=10, lang="de")
            rows["bm25_shipped"].append([bool(re.search(g, NORM(p["text"]), re.I)) for p in shipped])
            pin1 = retrieve_passages(chunks, q, top_k=10, lang="de", max_pins=1)
            rows["bm25_pin1"].append([bool(re.search(g, NORM(p["text"]), re.I)) for p in pin1])
            order, _ = bm25_rank(chunks, q)
            rows["bm25_plain"].append([rel[qi][i] for i in order[:10]])
            for name, (m, qp, pp) in models.items():
                qv = np.array(list(m.embed([qp + q])))[0]
                sims = emb[name] @ qv / (np.linalg.norm(emb[name], axis=1) * np.linalg.norm(qv))
                dense = list(np.argsort(-sims, kind="stable"))
                rows[f"dense_{name}"].append([rel[qi][i] for i in dense[:10]])
                rows[f"hybrid_{name}"].append([rel[qi][i] for i in rrf(order, dense)[:10]])
        results[size] = {"chunks": len(chunks), **{k: metrics(v) for k, v in rows.items()}}
    (HERE / "results" / "e30_rag_baselines.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    print("\nchunk  retriever             chunks  recall@1  recall@4  recall@6  recall@8  MRR@10  nDCG@10")
    for size, r in results.items():
        for k, v in r.items():
            if k == "chunks":
                continue
            print(f"{size:5d}  {k:20s} {r['chunks']:6d}  {v['recall@1']:8.2f}  {v['recall@4']:8.2f}  {v['recall@6']:8.2f}  {v['recall@8']:8.2f}  {v['mrr@10']:6.2f}  {v['ndcg@10']:7.2f}")


if __name__ == "__main__":
    main()
