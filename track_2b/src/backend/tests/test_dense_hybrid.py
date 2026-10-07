"""Optional hybrid retrieval (BM25 + dense, RRF) stays off by default and fuses rankings when a dense ranking exists."""

import graph.corpus as corpus
from graph import dense

CHUNKS = [
    {"source_id": f"d#{i}", "lang": "de", "is_question": False, "text": t}
    for i, t in enumerate([
        "Der Eigenmietwert wird abgeschafft und die Mindereinnahmen betragen rund 1,8 Milliarden Franken.",
        "Die Schuldzinsen können nur noch bei vermieteten Liegenschaften abgezogen werden.",
        "Das Referendum wurde ergriffen, deshalb kommt die E-ID zur Abstimmung.",
        "Die Stimmbeteiligung lag bei der letzten Abstimmung bei 45 Prozent.",
    ])
]


def test_dense_is_off_without_a_model_and_bm25_is_unchanged(monkeypatch):
    monkeypatch.delenv("EMBEDDING_MODEL", raising=False)
    assert dense.order(["a", "b"], "q") is None
    top = corpus.retrieve_passages(CHUNKS, "Mindereinnahmen Eigenmietwert", top_k=2, lang="de")
    assert top[0]["source_id"] == "d#0"


def test_rrf_prefers_items_ranked_well_by_both_rankings():
    assert dense.rrf([0, 1, 2, 3], [3, 1, 0, 2])[0] in (0, 1)  # 1 is 2nd in both, 0 is 1st and 3rd
    assert dense.rrf([2, 0], [2, 0]) == [2, 0]


def test_a_dense_ranking_can_rescue_a_question_bm25_misses(monkeypatch):
    # the query shares no word with the right chunk: BM25 scores it 0, the (fake) dense model ranks it first
    monkeypatch.setattr(corpus, "dense_order", lambda texts, query: [1, 0, 2, 3])
    top = corpus.retrieve_passages(CHUNKS, "Wie viel Geld fehlt dem Bund jaehrlich?", top_k=2, lang="de")
    assert any(c["source_id"] == "d#1" for c in top)
    monkeypatch.setattr(corpus, "dense_order", lambda texts, query: None)
    assert corpus.retrieve_passages(CHUNKS, "Wie viel Geld fehlt dem Bund jaehrlich?", top_k=2, lang="de") is not None
