sample_claimant_payload = {
    "full_name": "Juan Perez",
    "document_type": "CC",
    "document_number": "12345678",
    "email": "juan@example.com",
    "phone": "3001234567"
}

sample_ticket_payload = {
    "claimant": sample_claimant_payload,
    "free_text": "Este es un texto de prueba suficientemente largo para ser procesado como una petición formal.",
    "organization_id": "550e8400-e29b-41d4-a716-446655440000",
}
