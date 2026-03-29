from __future__ import annotations

import io


def test_upload_list_and_delete_document(client):
    upload_response = client.post(
        "/ingestion/upload",
        files=[("files", ("team.txt", io.BytesIO("Alice 2025 Q1 sales 500".encode("utf-8")), "text/plain"))],
        data={"team_id": "default", "tags": '["sales","2025"]', "parse_mode": "auto"},
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_ids"][0]

    list_response = client.get("/ingestion/documents")
    assert list_response.status_code == 200
    documents = list_response.json()["documents"]
    assert any(item["id"] == document_id for item in documents)

    delete_response = client.delete(f"/ingestion/{document_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["success"] is True

