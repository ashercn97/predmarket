from predmarket.core.models import Question, Contract, Platform

def test_question_model():
    question = Question(
        id="1",
        platform=Platform.POLIMARKET,
        title="Will a hot dog win the hot dog eating contest?",
    )
    assert question.id == "1"
    assert question.platform == Platform.POLIMARKET
    assert question.title == "Will a hot dog win the hot dog eating contest?"

def test_contract_model():
    contract = Contract(
        id="1",
        platform=Platform.KALSHI,
        question_id="2",
        outcomes=["Yes", "No"],
    )
    assert contract.id == "1"
    assert contract.platform == Platform.KALSHI
    assert contract.question_id == "2"
    assert contract.outcomes == ["Yes", "No"]
