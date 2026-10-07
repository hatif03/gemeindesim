"""Optional dense retrieval for hybrid (BM25 + embeddings, reciprocal rank fusion) search.

Research E30: on the 14 gold questions of the real 48-page booklet, BM25 as shipped finds the evidence in the top 6 for 12/14 questions, a
multilingual dense model (multilingual-e5-large) alone 14/14 at k = 4 and BM25 + dense fused with RRF 14/14 with the best ranking (MRR 0.91 vs 0.82).
It is off by default: neither inference endpoint offers embeddings (404/403), the model is a 2.2 GB local download and the app must also run
air-gapped. Enable with `EMBEDDING_MODEL=intfloat/multilingual-e5-large` and `pip install fastembed` (CPU, ONNX).
"""

from __future__ import annotations

import hashlib
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_MODEL: Any = None
_FAILED = False
_CACHE: dict[str, Any] = {}


def enabled() -> bool:
    return bool(os.environ.get("EMBEDDING_MODEL")) and not _FAILED


def _model() -> Any:
    global _MODEL, _FAILED
    if _MODEL is None:
        try:
            from fastembed import TextEmbedding

            _MODEL = TextEmbedding(model_name=os.environ["EMBEDDING_MODEL"])
        except Exception as exc:  # missing package, no network for the model download, unknown model id
            _FAILED = True
            logger.warning("dense retrieval disabled (BM25 only): %s", exc)
            raise
    return _MODEL


def _prefixes() -> tuple[str, str]:
    return ("query: ", "passage: ") if "e5" in os.environ.get("EMBEDDING_MODEL", "").lower() else ("", "")


def order(texts: list[str], query: str) -> list[int] | None:
    """Indices of `texts` from most to least similar to `query`; None when dense retrieval is off or unavailable."""
    if not enabled() or not texts:
        return None
    try:
        import numpy as np

        model = _model()
        qp, pp = _prefixes()
        keys = [hashlib.sha1((pp + t).encode()).hexdigest() for t in texts]
        missing = [i for i, k in enumerate(keys) if k not in _CACHE]
        if missing:
            for i, v in zip(missing, model.embed([pp + texts[i] for i in missing], batch_size=16)):
                _CACHE[keys[i]] = np.asarray(v, dtype=float)
        mat = np.stack([_CACHE[k] for k in keys])
        qv = np.asarray(next(iter(model.embed([qp + query]))), dtype=float)
        sims = mat @ qv / (np.linalg.norm(mat, axis=1) * np.linalg.norm(qv) + 1e-12)
        return [int(i) for i in np.argsort(-sims, kind="stable")]
    except Exception:
        return None


def rrf(*rankings: list[int], k: int = 60) -> list[int]:
    """Reciprocal rank fusion of several rankings of the same items."""
    score: dict[int, float] = {}
    for r in rankings:
        for pos, i in enumerate(r):
            score[i] = score.get(i, 0.0) + 1.0 / (k + pos + 1)
    return sorted(score, key=lambda i: -score[i])
