from __future__ import annotations

import io


def _seed_document(client):
    response = client.post(
        "/ingestion/upload",
        files=[("files", ("sales.txt", io.BytesIO("Alice 2025 Q1 sales 500 625 750 900".encode("utf-8")), "text/plain"))],
        data={"team_id": "default", "tags": '["sales"]', "parse_mode": "auto"},
    )
    return response.json()["document_ids"][0]


def test_retrieval_report_analysis_and_merge(client):
    document_id = _seed_document(client)

    search_response = client.post(
        "/retrieval/search",
        json={"query": "Alice sales", "top_k": 5, "hybrid_alpha": 0.7, "filters": {"tags": ["sales"]}},
    )
    assert search_response.status_code == 200
    assert search_response.json()["total_found"] >= 1

    report_response = client.post(
        "/report/generate",
        json={"entity": "Alice", "report_type": "person_profile", "include_sources": True, "max_sections": 3},
    )
    assert report_response.status_code == 200
    assert report_response.json()["title"].startswith("Alice")

    analysis_response = client.post(
        "/analysis/execute",
        json={"task": "Analyze sales trend", "document_ids": [document_id], "output_format": "json"},
    )
    assert analysis_response.status_code == 200
    assert "statistics" in analysis_response.json()["results"]

    merge_response = client.post(
        "/integration/merge",
        json={"document_ids": [document_id], "rule": {"strategy": "concatenate", "format": "markdown"}},
    )
    assert merge_response.status_code == 200
    assert merge_response.json()["source_count"] == 1

