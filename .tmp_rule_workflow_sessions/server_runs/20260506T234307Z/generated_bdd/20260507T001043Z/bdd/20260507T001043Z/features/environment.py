"""Behave environment hooks for LME Matching Rules BDD suite."""
from __future__ import annotations


def before_all(context):
    """Initialize LME test environment before any scenarios run."""
    # Import LME client stubs — replace with real LME client when VM access is available
    try:
        from lme_testing.step_library import LME_CLIENT
        context.lme = LME_CLIENT
    except ImportError:
        # Fallback: use mock client for demo
        class MockLME:
            Client = MockLMEClient()
            API = MockLMEAPI()
            PostTrade = MockLMEPostTrade()

        class MockLMEClient:
            def login(self, username=None, password=None):
                return MockSession()

        class MockLMEAPI:
            def submit_order(self, member, price=None):
                return MockResponse(status="submitted")
            def validate_price(self, trade):
                return MockValidationResult(status="passed")
            def contact_exchange(self, member, trade, rationale=None):
                return MockResponse(status="recorded")
            def get_contact_status(self, trade):
                return MockResponse(status="no_contact")
            def get_processing_record(self, trade):
                return {"record": "exists"}
            def submit_request(self, request):
                return MockResponse(status="accepted")
            def get_request_status(self, request):
                return "accepted"

        class MockLMEPostTrade:
            def create_trade(self, order):
                return MockTrade()
            def create_deadline(self):
                return {"timestamp": 1700000000}
            def create_request(self, deadline, offset_minutes=15):
                return MockRequest(deadline, offset_minutes)
            def validate_deadline(self, request):
                return MockValidationResult(result="pass")
            def get_obligation_status(self, trade):
                return "fulfilled"
            def get_outstanding_action(self, trade):
                return MockAction(type="contact_exchange", status="required")

        class MockSession:
            member_id = "TEST_MEMBER_001"
            token = "TEST_TOKEN"

        class MockTrade:
            id = "TRADE_001"
            status = "failed"

        class MockRequest:
            def __init__(self, deadline, offset_minutes):
                self.deadline = deadline
                self.offset_minutes = offset_minutes
                self.submitted_at = deadline["timestamp"] - (offset_minutes * 60)

        class MockAction:
            def __init__(self, type, status):
                self.type = type
                self.status = status

        class MockResponse:
            def __init__(self, status=None):
                self.status = status

        class MockValidationResult:
            def __init__(self, status=None, result=None):
                self.status = status
                self.result = result

        context.lme = MockLME()

    context.session = None
    context.member = None
    context.trade = None
    context.order = None
    context.request = None
    context.deadline = None
    context.contact_response = None
    context.validation_result = None


def before_scenario(context, scenario):
    """Reset context state before each scenario."""
    context.session = None
    context.member = None
    context.trade = None
    context.order = None
    context.request = None
    context.deadline = None
    context.contact_response = None
    context.validation_result = None
    context.agreements = []


def after_scenario(context, scenario):
    """Cleanup after each scenario (placeholder for real teardown)."""
    pass
