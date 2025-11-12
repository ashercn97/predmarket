import pytest
from unittest.mock import AsyncMock, MagicMock
from predmarket.client import UnifiedClient
from predmarket.core.models import Question, Contract, Platform
from predmarket.model.rest import Response

@pytest.fixture
def mock_kalshi_rest():
    mock = MagicMock()
    mock.fetch_questions = AsyncMock(
        return_value=Response(
            data=[
                Question(
                    id="1",
                    platform=Platform.KALSHI,
                    title="Kalshi Question 1",
                )
            ],
            metadata={},
        )
    )
    mock.fetch_contracts = AsyncMock(
        return_value=Response(
            data=[
                Contract(
                    id="1",
                    platform=Platform.KALSHI,
                    question_id="1",
                    outcomes=["Yes", "No"],
                )
            ],
            metadata={},
        )
    )
    return mock

@pytest.fixture
def mock_polymarket_rest():
    mock = MagicMock()
    mock.fetch_questions = AsyncMock(
        return_value=Response(
            data=[
                Question(
                    id="2",
                    platform=Platform.POLIMARKET,
                    title="Polymarket Question 1",
                )
            ],
            metadata={},
        )
    )
    mock.fetch_contracts = AsyncMock(
        return_value=Response(
            data=[
                Contract(
                    id="2",
                    platform=Platform.POLIMARKET,
                    question_id="2",
                    outcomes=["Yes", "No"],
                )
            ],
            metadata={},
        )
    )
    return mock

@pytest.mark.asyncio
async def test_unified_client_fetch_questions(mock_kalshi_rest, mock_polymarket_rest):
    client = UnifiedClient(mock_kalshi_rest, mock_polymarket_rest)
    questions = await client.fetch_questions()
    assert len(questions) == 2
    assert questions[0].platform == Platform.KALSHI
    assert questions[1].platform == Platform.POLIMARKET

@pytest.mark.asyncio
async def test_unified_client_fetch_contracts(mock_kalshi_rest, mock_polymarket_rest):
    client = UnifiedClient(mock_kalshi_rest, mock_polymarket_rest)
    contracts = await client.fetch_contracts()
    assert len(contracts) == 2
    assert contracts[0].platform == Platform.KALSHI
    assert contracts[1].platform == Platform.POLIMARKET
