import pytest
from pydantic import ValidationError
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from tests.conftest import make_mock_user, setup_auth_override, clear_auth_override


def _mock_llm(api_key="test-key", model="default-model", base_url="http://test"):
    mock = MagicMock()
    mock.config.api_key = api_key
    mock.config.model = model
    mock.config.base_url = base_url
    return mock


class TestGenerateMeetingPrepService:
    @pytest.mark.asyncio
    async def test_generate_meeting_prep_success(self):
        from gigaam_transcriber.meeting_prep.service import generate_meeting_prep

        mock_llm = _mock_llm(model="gpt-4o")
        mock_llm.call = MagicMock(
            return_value="# Информация о компании\n## История\nSome content"
        )

        result, model_used = await generate_meeting_prep(
            "Some company info", "Product catalog", mock_llm
        )

        assert "Информация о компании" in result
        assert model_used == "gpt-4o"
        mock_llm.call.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_meeting_prep_empty_response(self):
        from gigaam_transcriber.meeting_prep.service import generate_meeting_prep

        mock_llm = _mock_llm()
        mock_llm.call = MagicMock(return_value="")

        with pytest.raises(ValueError, match="пустой результат"):
            await generate_meeting_prep("info", "catalog", mock_llm)

    @pytest.mark.asyncio
    async def test_generate_meeting_prep_connection_error(self):
        from gigaam_transcriber.meeting_prep.service import generate_meeting_prep

        mock_llm = _mock_llm()
        mock_llm.call = MagicMock(side_effect=ConnectionError("Timeout"))

        with pytest.raises(ConnectionError, match="Timeout"):
            await generate_meeting_prep("info", "catalog", mock_llm)


class TestMeetingPrepSchema:
    def test_schema_validation_empty_company_data(self):
        from gigaam_transcriber.meeting_prep.schemas import MeetingPrepRequest

        with pytest.raises(ValidationError):
            MeetingPrepRequest(company_data="   ", catalog_data="valid catalog")

    def test_schema_validation_empty_catalog_data(self):
        from gigaam_transcriber.meeting_prep.schemas import MeetingPrepRequest

        with pytest.raises(ValidationError):
            MeetingPrepRequest(company_data="valid company", catalog_data="   ")

    def test_schema_valid_with_model(self):
        from gigaam_transcriber.meeting_prep.schemas import MeetingPrepRequest

        req = MeetingPrepRequest(
            company_data="data", catalog_data="cat", model="gpt-4o"
        )
        assert req.model == "gpt-4o"


@pytest.fixture(scope="module")
def client():
    mock_transcriber = MagicMock()
    with (
        patch("api.GigaAMTranscriber", return_value=mock_transcriber),
        patch("routers.meeting_prep.check_limit", new_callable=AsyncMock),
        patch("routers.meeting_prep.track_usage", new_callable=AsyncMock),
    ):
        from api import app
        from gigaam_transcriber.database import get_db

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        async def _mock_refresh(obj):
            obj.id = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"

        mock_db.refresh = _mock_refresh

        app.dependency_overrides[get_db] = lambda: mock_db
        setup_auth_override(app)

        with TestClient(app) as c:
            yield c

        app.dependency_overrides.clear()


class TestMeetingPrepEndpoint:
    def test_endpoint_unauthorized(self, client):
        from api import app

        clear_auth_override(app)
        try:
            resp = client.post(
                "/api/meeting-prep",
                json={"company_data": "info", "catalog_data": "cat"},
            )
        finally:
            setup_auth_override(app)

        assert resp.status_code in (401, 403, 422)

    def test_endpoint_success(self, client):
        mock_llm = _mock_llm()

        with (
            patch("routers.meeting_prep.llm_client", mock_llm),
            patch(
                "routers.meeting_prep.generate_meeting_prep",
                new=AsyncMock(
                    return_value=(
                        "# Report\n## Section 1\nContent here",
                        "gpt-4o",
                    )
                ),
            ),
        ):
            resp = client.post(
                "/api/meeting-prep",
                json={
                    "company_data": "Company info",
                    "catalog_data": "Product catalog",
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert "markdown" in data
        assert "model" in data
        assert data["model"] == "gpt-4o"
