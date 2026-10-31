from coding_agent.graph import _decision_is_approved, _latest_user_text
from langchain_core.messages import AIMessage, HumanMessage


def test_agentchatui_hitl_approve_payload():
    assert _decision_is_approved({"decisions": [{"type": "approve"}]})


def test_agentchatui_hitl_reject_payload():
    assert not _decision_is_approved({"decisions": [{"type": "reject"}]})


def test_rest_approval_payload():
    assert _decision_is_approved("approve")
    assert not _decision_is_approved("reject")


def test_latest_user_message_ignores_assistant_messages():
    messages = [
        HumanMessage(content="first request"),
        AIMessage(content="assistant reply"),
        HumanMessage(content="latest request"),
    ]
    assert _latest_user_text(messages) == "latest request"
