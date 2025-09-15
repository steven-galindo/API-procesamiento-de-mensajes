from fastapi import status


class TestMessagesEndpointIntegration:
    """test de integración para el endpoint/api/messages """

    def test_post_message_success(self, client, auth_headers, mock_corpus_file):
        """Mensaje de prueba exitoso"""
        #datos de ejemplo
        message_data = {
            "message_id": "msg-123456",
            "session_id": "session-abcdef", 
            "content": "Hola, ¿cómo puedo ayudarte hoy?",
            "timestamp": "2023-06-15T14:30:00Z",
            "sender": "system"
        }

        response = client.post("/api/messages/", json=message_data, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        
        response_data = response.json()
        assert response_data["status"] == "success"
        
        #verificar datos procesados
        data = response_data["data"]
        assert data["message_id"] == "msg-123456"
        assert data["session_id"] == "session-abcdef"
        assert data["content"] == "Hola, ¿cómo puedo ayudarte hoy?"
        assert data["timestamp"] == "2023-06-15T14:30:00Z"
        assert data["sender"] == "system"

        metadata = data["metadata"]
        assert metadata["word_count"] == 5  
        assert metadata["character_count"] == 31
        assert "processed_at" in metadata
        assert metadata["processed_at"] is not None

    def test_post_message_user_sender(self, client, auth_headers, mock_corpus_file):
        """Test envío de mensaje con remitente 'user'"""
        message_data = {
            "message_id": "msg-789012",
            "session_id": "session-xyz789",
            "content": "Necesito ayuda con mi cuenta",
            "timestamp": "2023-06-15T15:45:00Z",
            "sender": "user"
        }

        response = client.post("/api/messages/", json=message_data, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["status"] == "success"
        assert response_data["data"]["sender"] == "user"
        assert response_data["data"]["metadata"]["word_count"] == 5
        assert response_data["data"]["metadata"]["character_count"] == 28

    def test_post_message_with_special_characters(self, client, auth_headers, mock_corpus_file):
        """Test envío de mensaje con caracteres especiales y emojis"""
        message_data = {
            "message_id": "msg-special-001",
            "session_id": "session-special-test",
            "content": "¡Hola! 😊 ¿Cómo estás? Tengo una pregunta importante.",
            "timestamp": "2023-06-15T16:00:00Z",
            "sender": "user"
        }

        response = client.post("/api/messages/", json=message_data, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["status"] == "success"
        assert response_data["data"]["content"] == "¡Hola! 😊 ¿Cómo estás? Tengo una pregunta importante."

    def test_post_message_empty_content(self, client, auth_headers, mock_corpus_file):
        """Test envío de mensaje con contenido vacío"""
        message_data = {
            "message_id": "msg-empty-001",
            "session_id": "session-empty-test",
            "content": "",
            "timestamp": "2023-06-15T16:15:00Z",
            "sender": "user"
        }

        response = client.post("/api/messages/", json=message_data, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["status"] == "success"
        assert response_data["data"]["metadata"]["word_count"] == 0
        assert response_data["data"]["metadata"]["character_count"] == 0

    def test_post_message_long_content(self, client, auth_headers, mock_corpus_file):
        """Test envío de mensaje con contenido largo"""
        long_content = "Este es un mensaje muy largo que contiene muchas palabras. " * 20
        message_data = {
            "message_id": "msg-long-001",
            "session_id": "session-long-test",
            "content": long_content,
            "timestamp": "2023-06-15T16:30:00Z",
            "sender": "user"
        }

        response = client.post("/api/messages/", json=message_data, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["status"] == "success"
        assert response_data["data"]["metadata"]["word_count"] > 100
        assert response_data["data"]["metadata"]["character_count"] > 500

    def test_post_message_without_auth(self, client, mock_corpus_file):
        """Test mensaje sin autenticación"""
        message_data = {
            "message_id": "msg-unauthorized",
            "session_id": "session-unauthorized",
            "content": "This should fail",
            "timestamp": "2023-06-15T17:00:00Z",
            "sender": "user"
        }

        response = client.post("/api/messages/", json=message_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_post_message_invalid_api_key(self, client, mock_corpus_file):
        """Test envío de mensaje con API key inválida"""
        message_data = {
            "message_id": "msg-invalid-key",
            "session_id": "session-invalid-key",
            "content": "This should fail",
            "timestamp": "2023-06-15T17:15:00Z",
            "sender": "user"
        }

        invalid_headers = {"X-API-Key": "invalid-key"}
        response = client.post("/api/messages/", json=message_data, headers=invalid_headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_post_message_invalid_sender(self, client, auth_headers, mock_corpus_file):
        """Test envío de mensaje con valor de remitente inválido"""
        message_data = {
            "message_id": "msg-invalid-sender",
            "session_id": "session-invalid-sender",
            "content": "Test message",
            "timestamp": "2023-06-15T17:30:00Z",
            "sender": "sender" 
        }

        response = client.post("/api/messages/", json=message_data, headers=auth_headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_post_message_missing_required_fields(self, client, auth_headers, mock_corpus_file):
        """Test envío de mensaje con campos requeridos faltantes"""
        # sin id
        incomplete_data = {
            "session_id": "session-incomplete",
            "content": "Test message",
            "timestamp": "2023-06-15T17:45:00Z",
            "sender": "user"
        }

        response = client.post("/api/messages/", json=incomplete_data, headers=auth_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_post_message_banned_content(self, client, auth_headers, mock_corpus_file):
        """Test message processing with banned words"""
        message_data = {
            "message_id": "msg-banned-001",
            "session_id": "session-banned-test",
            "content": "Este es un mensaje sobre scam y fraude",
            "timestamp": "2023-06-15T18:00:00Z",
            "sender": "user"
        }

        response = client.post("/api/messages/", json=message_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_post_multiple_messages_same_session(self, client, auth_headers, mock_corpus_file):
        """Test posting multiple messages to the same session"""
        session_id = "session-multi-test"
        
        messages = [
            {
                "message_id": "msg-multi-001",
                "session_id": session_id,
                "content": "Primer mensaje",
                "timestamp": "2023-06-15T18:15:00Z",
                "sender": "user"
            },
            {
                "message_id": "msg-multi-002", 
                "session_id": session_id,
                "content": "Segundo mensaje de respuesta",
                "timestamp": "2023-06-15T18:16:00Z",
                "sender": "system"
            }
        ]

        for message_data in messages:
            response = client.post("/api/messages/", json=message_data, headers=auth_headers)
            assert response.status_code == status.HTTP_200_OK
            assert response.json()["status"] == "success"

    def test_post_message_edge_case_unicode(self, client, auth_headers, mock_corpus_file):
        """Test envío de mensaje con varios caracteres Unicode"""
        message_data = {
            "message_id": "msg-unicode-001",
            "session_id": "session-unicode-test",
            "content": "测试 тест اختبار  नमस्ते مرحبا",
            "timestamp": "2023-06-15T18:30:00Z",
            "sender": "user"
        }

        response = client.post("/api/messages/", json=message_data, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["status"] == "success"
        assert response_data["data"]["content"] == "测试 тест اختبار  नमस्ते مرحبا"

    def test_response_time_performance(self, client, auth_headers, mock_corpus_file):
        """Test tiempo de respeuesta del endpoint"""
        import time
        
        message_data = {
            "message_id": "msg-perf-001",
            "session_id": "session-perf-test",
            "content": "Performance test message",
            "timestamp": "2023-06-15T19:00:00Z",
            "sender": "user"
        }

        start_time = time.time()
        response = client.post("/api/messages/", json=message_data, headers=auth_headers)
        end_time = time.time()

        assert response.status_code == status.HTTP_200_OK
        response_time = end_time - start_time #calcular tiempo de respuesta
        assert response_time < 2.0 #menos de 2 segundos