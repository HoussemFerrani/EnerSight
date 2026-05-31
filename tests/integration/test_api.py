"""
Integration Tests for API Endpoints
Tests full request/response cycle with FastAPI
"""

import pytest
from fastapi import status


@pytest.mark.api
@pytest.mark.integration
class TestRootEndpoints:
    """Test root and health endpoints"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns API information"""
        # Act
        response = client.get("/")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "application" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "operational"
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        # Act
        response = client.get("/health")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "components" in data
        assert "version" in data
    
    def test_api_info_endpoint(self, client):
        """Test API info endpoint"""
        # Act
        response = client.get("/api/v1/info")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "api_version" in data
        assert "features" in data
        assert "ml_models" in data
        assert isinstance(data["features"], list)
        assert isinstance(data["ml_models"], dict)


@pytest.mark.api
@pytest.mark.integration
class TestErrorHandling:
    """Test error handling and exception responses"""
    
    def test_404_not_found(self, client):
        """Test 404 error for non-existent endpoint"""
        # Act
        response = client.get("/api/v1/nonexistent")
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "HTTP_404"
    
    def test_invalid_json_request(self, client):
        """Test invalid JSON in request body"""
        # Act
        response = client.post(
            "/api/v1/energy/readings",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        # Assert - Should handle gracefully
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_404_NOT_FOUND,  # If route not implemented yet
        ]


@pytest.mark.api
@pytest.mark.integration
class TestCORS:
    """Test CORS configuration"""
    
    def test_cors_headers_present(self, client):
        """Test CORS headers are included in responses"""
        # Act - CORSMiddleware only emits CORS headers when an Origin is sent
        response = client.get("/", headers={"Origin": "http://localhost:3000"})

        # Assert
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-credentials" in response.headers
    
    def test_options_request(self, client):
        """Test CORS preflight OPTIONS request"""
        # Act
        response = client.options(
            "/api/v1/info",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            }
        )
        
        # Assert
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_405_METHOD_NOT_ALLOWED]


@pytest.mark.api
@pytest.mark.slow
@pytest.mark.asyncio
class TestAsyncEndpoints:
    """Test async endpoints with async client"""
    
    async def test_health_check_async(self, async_client):
        """Test health check with async client"""
        # Act
        response = await async_client.get("/health")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data
    
    async def test_concurrent_requests(self, async_client):
        """Test handling multiple concurrent requests"""
        import asyncio
        
        # Act - Send 10 concurrent requests
        tasks = [
            async_client.get("/api/v1/info")
            for _ in range(10)
        ]
        responses = await asyncio.gather(*tasks)
        
        # Assert - All should succeed
        assert len(responses) == 10
        for response in responses:
            assert response.status_code == status.HTTP_200_OK


@pytest.mark.api
@pytest.mark.integration
class TestResponseFormat:
    """Test response format consistency"""
    
    def test_successful_response_format(self, client):
        """Test successful responses have consistent format"""
        # Act
        response = client.get("/api/v1/info")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/json"
        
        # Should be valid JSON
        data = response.json()
        assert isinstance(data, dict)
    
    def test_error_response_format(self, client):
        """Test error responses have consistent format"""
        # Act
        response = client.get("/api/v1/nonexistent")
        
        # Assert
        data = response.json()
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
        assert "type" in data["error"]


@pytest.mark.api
@pytest.mark.integration
class TestPerformance:
    """Test API performance characteristics"""
    
    def test_response_time(self, client):
        """Test response time is acceptable"""
        import time
        
        # Act
        start = time.time()
        response = client.get("/health")
        end = time.time()
        
        # Assert - Should respond in < 100ms
        assert response.status_code == status.HTTP_200_OK
        assert (end - start) < 0.1, "Response took too long"
    
    @pytest.mark.slow
    def test_multiple_sequential_requests(self, client):
        """Test handling multiple sequential requests"""
        # Act
        responses = [
            client.get("/health")
            for _ in range(100)
        ]
        
        # Assert - All should succeed
        assert len(responses) == 100
        for response in responses:
            assert response.status_code == status.HTTP_200_OK


# ==================== Future Test Placeholders ====================

@pytest.mark.skip(reason="Energy endpoint not yet implemented")
class TestEnergyEndpoints:
    """Tests for energy data endpoints (TODO)"""
    
    def test_get_energy_readings(self, client):
        """Test retrieving energy readings"""
        pass
    
    def test_post_energy_reading(self, client):
        """Test creating new energy reading"""
        pass
    
    def test_get_energy_statistics(self, client):
        """Test energy statistics endpoint"""
        pass


@pytest.mark.skip(reason="Prediction endpoint not yet implemented")
class TestPredictionEndpoints:
    """Tests for ML prediction endpoints (TODO)"""
    
    def test_predict_consumption(self, client):
        """Test consumption prediction"""
        pass
    
    def test_forecast_consumption(self, client):
        """Test time-series forecasting"""
        pass


@pytest.mark.skip(reason="Anomaly endpoint not yet implemented")
class TestAnomalyEndpoints:
    """Tests for anomaly detection endpoints (TODO)"""
    
    def test_get_anomalies(self, client):
        """Test retrieving anomalies"""
        pass
    
    def test_detect_anomalies(self, client):
        """Test anomaly detection"""
        pass
