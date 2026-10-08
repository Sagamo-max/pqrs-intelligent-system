import pytest

@pytest.mark.integration
def test_get_audit_success(client, seed_areas, sample_ticket_payload, mock_openai_classification):
    mock_openai_classification()
    create_resp = client.post("/api/v1/pqrs/", json=sample_ticket_payload)
    tracking = create_resp.json()["tracking_number"]
    
    resp = client.get(f"/api/v1/pqrs/{tracking}/audit")
    assert resp.status_code == 200
    assert resp.json()["decision_justification"].startswith("Mocked justification")

@pytest.mark.integration
def test_get_audit_not_found_ticket(client):
    resp = client.get("/api/v1/pqrs/INVALID-123/audit")
    assert resp.status_code == 404

@pytest.mark.integration
def test_get_audit_no_audit(client, seed_areas, sample_ticket_payload, mock_openai_classification, db_session, mocker):
    mock_openai_classification()
    create_resp = client.post("/api/v1/pqrs/", json=sample_ticket_payload)
    tracking = create_resp.json()["tracking_number"]
    
    from app.models.audit import AIAudit
    db_session.query(AIAudit).delete()
    db_session.commit()
    
    resp = client.get(f"/api/v1/pqrs/{tracking}/audit")
    assert resp.status_code == 404

