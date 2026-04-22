"""BDD export utilities for generating Gherkin feature files and Ruby step definitions."""

from __future__ import annotations

import re
from pathlib import Path


# Template registry for common BDD patterns
# These serve as the "learning" base for generating step definitions
TEMPLATE_REGISTRY: dict[str, dict] = {
    # Session/Login patterns
    "session_login": {
        "given_pattern": "a member with valid LME session",
        "given_code": '''Given(/^a member with valid LME session$/) do
  @session = LME::Client.login
end''',
    },
    "session_login_with_credentials": {
        "given_pattern": "a member with valid credentials",
        "given_code": '''Given(/^a member with valid credentials$/) do
  @session = LME::Client.login(username: @test_data[:username], password: @test_data[:password])
end''',
    },
    # Order/Trade patterns
    "order_submit": {
        "when_pattern": "member submits an order",
        "when_code": '''When(/^member submits an order$/) do
  @response = @session.submit_order(@order_params)
end''',
    },
    "order_fails_validation": {
        "when_pattern": "order fails price validation",
        "when_code": '''When(/^order fails price validation$/) do
  @order_params[:price] = '999999'  # Intentionally invalid
  @response = @session.submit_order(@order_params)
  expect(@response.status).to eq(:rejected)
end''',
    },
    # Exchange contact patterns
    "contact_exchange": {
        "then_pattern": "member contacts Exchange",
        "then_code": '''Then(/^member contacts Exchange$/) do
  expect(LME::PostTrade).to receive(:contact_exchange).with(kind_of(String))
  LME::PostTrade.contact_exchange(reason: @response.rejection_reason)
end''',
    },
    "exchange_records_contact": {
        "then_pattern": "Exchange records the contact",
        "then_code": '''Then(/^Exchange records the contact$/) do
  contact = LME::PostTrade.get_contact(reason: @response.rejection_reason)
  expect(contact).not_to be_nil
  expect(contact[:member_id]).to eq(@session.member_id)
end''',
    },
    # Deadline patterns
    "within_deadline": {
        "then_pattern": "within deadline",
        "then_code": '''Then(/^within deadline$/) do
  expect(@action.completed_at - @action.started_at).to be < @deadline_seconds
end''',
    },
    # API call patterns
    "api_get": {
        "when_pattern": "GET request to",
        "when_code": '''When(/^GET request to (.+)$/) do |endpoint|
  @response = LME::API.get(endpoint, @session.token)
end''',
    },
    "api_post": {
        "when_pattern": "POST request to",
        "when_code": '''When(/^POST request to (.+) with (.+)$/) do |endpoint, payload|
  @response = LME::API.post(endpoint, @session.token, JSON.parse(payload))
end''',
    },
    "api_response_success": {
        "then_pattern": "API response should be successful",
        "then_code": '''Then(/^API response should be successful$/) do
  expect(@response.status).to be_between(200, 299)
end''',
    },
    "api_response_contains": {
        "then_pattern": "response contains",
        "then_code": '''Then(/^response contains (.+)$/) do |field|
  expect(@response.body).to have_key(field)
end''',
    },
    # Web/Selenium patterns
    "web_navigate": {
        "when_pattern": "navigates to",
        "when_code": '''When(/^navigates to (.+)$/) do |url|
  @browser.goto(url)
end''',
    },
    "web_click": {
        "when_pattern": "clicks on",
        "when_code": '''When(/^clicks on (.+)$/) do |element|
  @browser.element(visible_text: element).click
end''',
    },
    "web_see": {
        "then_pattern": "should see",
        "then_code": '''Then(/^should see (.+)$/) do |text|
  expect(@browser.text).to include(text)
end''',
    },
    # Terminology validation patterns (learned from samples/ruby_cucumber/)
    "terminology_assigned": {
        "given_pattern": "terms are assigned the meaning ascribed in the LME Rulebook",
        "given_code": '''Given(/^the terms are assigned the meaning ascribed in the LME Rulebook$/) do
  @validation_result = LME::API.validate_terminology(@document)
end''',
    },
    "terminology_compliant": {
        "then_pattern": "terms are assigned the meaning ascribed in the LME Rulebook",
        "then_code": '''Then(/^the terms are assigned the meaning ascribed in the LME Rulebook$/) do
  expect(@validation_result.compliant).to be(true)
  expect(@validation_result.source).to eq('LME Rulebook')
end''',
    },
    "terminology_deviation": {
        "then_pattern": "system identifies the deviation from the LME Rulebook",
        "then_code": '''Then(/^the system identifies the deviation from the LME Rulebook$/) do
  expect(@validation_result.compliant).to be(false)
  expect(@validation_result.errors).to include('TERM_DEVIATION')
end''',
    },
    "obligation_fulfilled": {
        "then_pattern": "obligation is fulfilled",
        "then_code": '''Then(/^the obligation is fulfilled$/) do
  expect(@validation_result.status).to eq('fulfilled')
end''',
    },
    "obligation_not_fulfilled": {
        "then_pattern": "obligation is not fulfilled",
        "then_code": '''Then(/^the obligation is not fulfilled$/) do
  expect(@validation_result.status).to eq('rejected')
end''',
    },
    # Price validation contact workflow (learned from samples/ruby_cucumber/)
    "contact_exchange_reason": {
        "when_pattern": "member contacts Exchange to explain",
        "when_code": '''When(/^the Member contacts the Exchange to explain the rationale for the price$/) do
  @contact_response = LME::PostTrade.contact_exchange(
    reason: @validation_result.rejection_reason
  )
end''',
    },
    "compliance_recorded": {
        "then_pattern": "processing result indicates compliance",
        "then_code": '''Then(/^the processing result indicates compliance$/) do
  expect(@contact_response).not_to be_nil
  expect(@contact_response.status).to eq('RECORDED')
  compliance = LME::PostTrade.get_compliance_status(@validation_result.rejection_reason)
  expect(compliance).to eq('COMPLIANT')
end''',
    },
    "non_compliance": {
        "then_pattern": "processing result indicates non-compliance",
        "then_code": '''Then(/^the processing result indicates non-compliance or failure$/) do
  expect(@contact_response).to be_nil
  compliance = LME::PostTrade.get_compliance_status('trade_without_contact')
  expect(compliance).to eq('NON_COMPLIANT')
end''',
    },
    # Trade re-submission patterns (learned from samples/ruby_cucumber/)
    "trade_failed_checks": {
        "given_pattern": "trade submission resulted in Failed Checks",
        "given_code": '''Given(/^trade submission resulted in Failed Checks$/) do
  @trade_params = { price: '999999', metal: 'ALU', quantity: 25 }
  @trade_submission = LME::API.submit_trade(@trade_params)
  expect(@trade_submission.status).to eq('SUBMITTED')
end''',
    },
    "resubmit_original_form": {
        "when_pattern": "Member requests to re-submit the trade in its original form",
        "when_code": '''When(/^Member requests to re-submit the trade in its original form$/) do
  @resubmission_response = LME::API.resubmit_trade(
    @trade_submission.id, original_form: @trade_params
  )
end''',
    },
    "resubmission_permitted": {
        "then_pattern": "system permits the trade re-submission",
        "then_code": '''Then(/^system permits the trade re-submission$/) do
  expect(@resubmission_response.status).to eq('PERMITTED')
end''',
    },
    # Venue-specific validation patterns
    "venue_business_transacted": {
        "given_pattern": "business is transacted on the Exchange",
        "given_code": '''Given(/^business is transacted on the Exchange$/) do
  @session = LME::Client.login(
    username: ENV['LME_USERNAME'] || 'test_trader',
    password: ENV['LME_PASSWORD'] || 'test_pass'
  )
end''',
    },
    "venue_trade_agreement": {
        "when_pattern": "trade agreement occurs",
        "when_code": '''When(/^trade agreement occurs$/) do
  @trade_agreement = LME::PostTrade.create_agreement
end''',
    },
    "venue_price_validation": {
        "then_pattern": "business is subject to price validation",
        "then_code": '''Then(/^business is subject to price validation$/) do
  expect(@trade_agreement.price_validation_required).to be(true)
end''',
    },
    # Matching rules adoption patterns
    "exchange_defines_matching_rules": {
        "given_pattern": "Exchange defines matching rules",
        "given_code": '''Given(/^the Exchange defines matching rules$/) do
  @rules = LME::PostTrade.define_matching_rules(version: '1.0')
end''',
    },
    "rules_submitted_adoption": {
        "when_pattern": "rules are submitted for adoption",
        "when_code": '''When(/^the rules are submitted for adoption$/) do
  @adoption_status = LME::PostTrade.submit_adoption(@rules)
end''',
    },
    "rules_adopted": {
        "then_pattern": "rules are recognized as part of Administrative Procedures",
        "then_code": '''Then(/^the rules are recognized as part of Administrative Procedures$/) do
  expect(@adoption_status.adopted).to be(true)
  expect(@adoption_status.classification).to eq('Administrative_Procedures')
end''',
    },
    # LME trading environment
    "lme_environment_active": {
        "given_pattern": "LME trading environment is active",
        "given_code": '''Given(/^LME trading environment is active$/) do
  @env = LME::Client.environment
  expect(@env.status).to eq('active')
end''',
    },
    "trade_on_any_venue": {
        "when_pattern": "trade agreement occurs on any venue",
        "when_code": '''When(/^trade agreement occurs on any venue$/) do
  @agreement = LME::PostTrade.create_agreement
end''',
    },
    "trade_subject_to_validation": {
        "then_pattern": "trade is subject to price validation",
        "then_code": '''Then(/^trade is subject to price validation$/) do
  expect(@agreement.price_validation_required).to be(true)
end''',
    },
}


def sanitize_filename(text: str) -> str:
    """Convert text to safe filename."""
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s]+', '_', text)
    return text.lower()[:50]


def build_tags(case_type: str, priority: str) -> list[str]:
    """Build Gherkin tags from case_type and priority."""
    tags = [f"@{case_type}"]
    if priority in ("high", "critical"):
        tags.append("@priority_high")
    return tags


def render_given_step(step: str) -> str:
    """Render a single Given step."""
    return f"    Given {step}"


def render_when_step(step: str) -> str:
    """Render a single When step."""
    return f"    When {step}"


def render_then_step(step: str) -> str:
    """Render a single Then step."""
    return f"    Then {step}"


def render_and_step(step: str) -> str:
    """Render an And step (same indentation as the previous step type)."""
    return f"    And {step}"


def render_scenario(scenario: dict, feature_id: str) -> str:
    """Render a single Gherkin Scenario."""
    lines = []

    scenario_id = scenario.get("scenario_id", "unknown")
    title = scenario.get("title", scenario.get("intent", "Unnamed scenario"))
    case_type = scenario.get("case_type", "positive")
    priority = scenario.get("priority", "medium")

    tags = build_tags(case_type, priority)
    lines.append(f"  {' '.join(tags)}  # {scenario_id}")

    lines.append(f"  Scenario: {title}")

    given_steps = scenario.get("given", [])
    when_steps = scenario.get("when", [])
    then_steps = scenario.get("then", [])
    assumptions = scenario.get("assumptions", [])

    # Combine assumptions with given steps (assumptions are pre-conditions)
    all_given_steps = assumptions + given_steps

    prev_step_keyword = None
    for i, step in enumerate(all_given_steps):
        if i == 0:
            lines.append(render_given_step(step))
            prev_step_keyword = "Given"
        else:
            lines.append(render_and_step(step))

    for i, step in enumerate(when_steps):
        if i == 0:
            lines.append(render_when_step(step))
        else:
            lines.append(render_and_step(step))

    for i, step in enumerate(then_steps):
        if i == 0:
            lines.append(render_then_step(step))
        else:
            lines.append(render_and_step(step))

    return "\n".join(lines)


def render_feature_file(semantic_rule_id: str, feature_title: str, scenarios: list[dict], intent: str = "") -> str:
    """Render a complete Gherkin Feature file."""
    lines = []

    lines.append(f"Feature: {feature_title}")
    lines.append(f"  {semantic_rule_id}")

    if intent:
        lines.append(f"  {intent}")

    lines.append("")

    for scenario in scenarios:
        lines.append(render_scenario(scenario, semantic_rule_id))
        lines.append("")

    return "\n".join(lines)


def extract_step_pattern(step: str) -> str:
    """Extract a regex pattern from a step string (without anchors)."""
    # Convert Gherkin step to regex pattern
    pattern = step
    pattern = re.sub(r'\b(a|an|the)\b', '(?:a|an|the)', pattern, flags=re.IGNORECASE)
    pattern = re.sub(r'\b\d+\b', lambda m: r'\d+', pattern)
    return pattern


def _step_tokens(text: str) -> set[str]:
    """Return significant (non-stopword) tokens from step text for matching."""
    stopwords = {"a", "an", "the", "to", "is", "are", "be", "that", "this", "it", "of", "in", "for", "on", "and", "or", "with", "as", "at", "by"}
    return {w for w in re.findall(r'\w+', text.lower()) if w not in stopwords and len(w) > 2}


def map_step_to_template(step: str, step_type: str, require_exact: bool = False) -> str | None:
    """Map a step to a known template if available.

    Uses multi-strategy matching:
    - exact substring match (fast path for common patterns)
    - token-overlap match (handles rephrasing)
    - parameterized prefix match (handles "GET request to /path" variants)

    When require_exact=True (used for human-edited steps), only exact substring
    matches are accepted to avoid applying wrong templates.
    """
    step_lower = step.lower()

    for template in TEMPLATE_REGISTRY.values():
        pattern_field = f"{step_type}_pattern"
        if pattern_field not in template:
            continue
        pattern = template[pattern_field]
        pattern_lower = pattern.lower()

        if require_exact:
            # Strict: only accept exact or near-exact substring match
            if pattern_lower in step_lower or step_lower in pattern_lower:
                return template.get(f"{step_type}_code")
            continue

        # Flexible matching (original behavior + improvements)
        # 1. Exact substring (either direction)
        if pattern_lower in step_lower or step_lower in pattern_lower:
            return template.get(f"{step_type}_code")

        # 2. Parameterized prefix: "GET request to" matches "GET request to /api/users"
        if "(" not in pattern:
            # Non-parameterized pattern — check prefix overlap
            words = pattern_lower.split()
            if len(words) >= 2 and step_lower.startswith(" ".join(words[:2])):
                return template.get(f"{step_type}_code")

        # 3. Token overlap: require at least 2 significant words in common
        pattern_toks = _step_tokens(pattern)
        step_toks = _step_tokens(step)
        overlap = pattern_toks & step_toks
        if len(overlap) >= 2 and len(pattern_toks) >= 2:
            # Only accept if the overlap represents meaningful content (not common filler)
            if len(overlap) / len(pattern_toks) >= 0.4:
                return template.get(f"{step_type}_code")

    return None


def generate_step_definition(
    step: str,
    step_type: str,
    step_index: int,
    feature_name: str,
    human_edited: bool = False,
) -> str:
    """Generate Python step definition code for a given step.

    Uses STEP_LIBRARY (from step_library.py) as the primary source of canonical
    implementations. Falls back to _generate_python_implementation for steps
    not in the library.

    Args:
        step: The Gherkin step text (e.g., "member submits an order").
        step_type: One of "given", "when", "then".
        step_index: Index of this step within its type group (for disambiguation).
        feature_name: Name of the feature this step belongs to.
        human_edited: If True, prefer template matches even when not exact.
                      Used when a human has manually reviewed and customized the step.
    """
    from .step_library import STEP_LIBRARY

    step_lower = step.lower()

    # 1. Exact lookup in STEP_LIBRARY
    if step in STEP_LIBRARY:
        return STEP_LIBRARY[step].render()

    # 2. Try map_step_to_template (legacy Ruby templates — convert to Python stub)
    template_code = map_step_to_template(step, step_type, require_exact=not human_edited)
    if template_code:
        # Convert Ruby template to Python equivalent (use library entry if available)
        # Ruby: Given(/^...$/) do ... end  →  Python: @given("...")\ndef step():
        #     ...
        # For now, generate a Python stub with the same logic
        pass  # falls through to implementation generator

    # 3. Generate from implementation heuristics
    pattern = extract_step_pattern(step)
    generated = _generate_python_implementation(step, step_type, pattern, step)
    if generated:
        return generated

    # 4. Fall back to Python pending stub
    safe_name = re.sub(r"[^\w]", "_", step_lower)[:50].strip("_")
    keyword = step_type.lower()
    return f'''@{keyword}("{_escape_py_str(step)}")
def {safe_name or "unnamed_step"}():
    # TODO: implement step: {step}
    pass'''


def _escape_py_str(text: str) -> str:
    """Escape a string for use in a Python single-quoted literal."""
    return text.replace("\\", "\\\\").replace("'", "\\'")


def _generate_python_implementation(step: str, step_type: str, pattern: str, step_text: str) -> str | None:
    """Attempt to generate a Python step implementation based on step text analysis.

    Returns None if no meaningful implementation can be generated.
    All generated code uses Python syntax with LME.Client, LME.API, LME.PostTrade.
    """
    step_lower = step.lower()
    keyword = step_type.lower()

    def py(code: str) -> str:
        return f'@{keyword}("{_escape_py_str(step_text)}")\ndef {code}'

    if step_type == "given":
        if "session" in step_lower or "login" in step_lower or "member" in step_lower:
            return py(f'''step_member_session():
    session = LME.Client.login(
        username=ENV.get('LME_USERNAME', 'test_trader'),
        password=ENV.get('LME_PASSWORD', 'test_pass'),
    )
    return session''')
        if "environment" in step_lower and "active" in step_lower:
            return py('''step_environment_active():
    env = LME.Client.environment
    assert env.status == 'active' ''')
        if "trade" in step_lower or "submission" in step_lower:
            return py('''step_trade_submission():
    trade_params = {
        'price': '999999',
        'metal': 'ALU',
        'quantity': 25,
    }
    trade_submission = LME.API.submit_trade(trade_params)''')
        if "document" in step_lower or "terminology" in step_lower or "terms" in step_lower:
            return py('''step_document_terminology():
    document = LME.API.create_document(broker=broker, terms='capitalised')''')
        if "exchange" in step_lower and "matching rules" in step_lower:
            return py('''step_exchange_defines_rules():
    rules = LME.PostTrade.define_matching_rules(version='1.0')''')
        if "deadline" in step_lower:
            return py('''step_deadline_exists():
    deadline = LME.PostTrade.get_deadline(request_type='post_trade_correction')
    assert deadline is not None''')

    elif step_type == "when":
        if "contact" in step_lower and "exchange" in step_lower:
            return py('''step_contacts_exchange():
    contact_response = LME.PostTrade.contact_exchange(
        reason=validation_result.rejection_reason,
        member=session.member_id,
    )
    return contact_response''')
        if "api" in step_lower and "get" in step_lower:
            return py('''step_api_get():
    response = LME.API.get(endpoint, session.token)
    return response''')
        if "api" in step_lower and "post" in step_lower:
            return py('''step_api_post():
    import json
    response = LME.API.post(endpoint, session.token, json.loads(payload))
    return response''')
        if "submit" in step_lower or "submits" in step_lower:
            return py('''step_submit_order():
    response = session.submit_order(order_params)
    return response''')
        if "trade" in step_lower and ("agreement" in step_lower or "occur" in step_lower):
            return py('''step_trade_agreement():
    trade_agreement = LME.PostTrade.create_agreement()
    return trade_agreement''')
        if "rules" in step_lower and "adoption" in step_lower:
            return py('''step_rules_adoption():
    adoption_status = LME.PostTrade.submit_adoption(rules)
    return adoption_status''')
        if "re-submit" in step_lower or "resubmit" in step_lower:
            return py('''step_resubmit_trade():
    resubmission_response = LME.API.resubmit_trade(
        trade_submission.id,
        original_form=trade_params,
    )
    return resubmission_response''')
        if "request" in step_lower and "deadline" in step_lower:
            # Try to extract minute count from step text
            m = re.search(r"(\d+)\s+minutes?", step_lower)
            minutes = m.group(1) if m else "15"
            return py(f'''step_request_before_deadline():
    deadline_ts = deadline.get('timestamp')
    submitted_at = deadline_ts - ({minutes} * 60)
    response = LME.API.submit_request(
        request_type='post_trade_correction',
        submitted_at=submitted_at,
        session=session,
    )''')

    elif step_type == "then":
        if "price validation" in step_lower and "subject" in step_lower:
            return py('''step_price_validation_subject():
    assert trade_agreement.price_validation_required is True''')
        if ("compliance" in step_lower or "compliant" in step_lower) and "not" not in step_lower:
            return py('''step_compliance_recorded():
    assert contact_response is not None
    assert contact_response.status == 'RECORDED'
    compliance = LME.PostTrade.get_compliance_status(validation_result.rejection_reason)
    assert compliance == 'COMPLIANT' ''')
        if "non-compliance" in step_lower or ("not" in step_lower and "compliant" in step_lower):
            return py('''step_non_compliance():
    assert contact_response is None
    compliance = LME.PostTrade.get_compliance_status('trade_without_contact')
    assert compliance == 'NON_COMPLIANT' ''')
        if "obligation" in step_lower and "fulfilled" in step_lower:
            return py('''step_obligation_fulfilled():
    assert validation_result.status == 'fulfilled' ''')
        if "obligation" in step_lower and ("not" in step_lower or "rejected" in step_lower):
            return py('''step_obligation_not_fulfilled():
    assert validation_result.status == 'rejected' ''')
        if "terminology" in step_lower or ("terms" in step_lower and "rulebook" in step_lower):
            return py('''step_terminology_rulebook():
    assert validation_result.compliant is True
    assert validation_result.source == 'LME Rulebook' ''')
        if "deviation" in step_lower:
            return py('''step_deviation_detected():
    assert validation_result.compliant is False
    assert 'TERM_DEVIATION' in validation_result.errors ''')
        if "re-submission" in step_lower or "resubmit" in step_lower:
            return py('''step_resubmission_permitted():
    assert resubmission_response.status == 'PERMITTED' ''')
        if "accepted" in step_lower and "request" in step_lower:
            return py('''step_request_accepted():
    assert response.status == 'accepted' ''')
        if "rejected" in step_lower and "late" in step_lower:
            return py('''step_request_rejected_late():
    assert response.status == 'rejected'
    assert response.rejection_reason == 'late_submission' ''')
        if "deadline" in step_lower and ("pass" in step_lower or "success" in step_lower):
            return py('''step_deadline_pass():
    result = LME.API.get_deadline_validation(response.request_id)
    assert result in ('pass', 'PASS', True) ''')
        if "deadline" in step_lower and ("fail" in step_lower or "failure" in step_lower):
            return py('''step_deadline_fail():
    result = LME.API.get_deadline_validation(response.request_id)
    assert result in ('fail', 'FAIL', False) ''')
        if "recorded" in step_lower and "timestamp" in step_lower:
            return py('''step_timestamp_recorded():
    submitted_at = response.submitted_at
    deadline_ts = deadline.get('timestamp')
    assert submitted_at <= deadline_ts - (15 * 60) ''')
        if "recorded" in step_lower and ("late" in step_lower or "submission" in step_lower):
            return py('''step_late_submission_recorded():
    outcome = LME.PostTrade.get_submission_outcome('late_submission')
    assert outcome is not None ''')
        if "api" in step_lower and "successful" in step_lower:
            return py('''step_api_success():
    assert 200 <= response.status < 300 ''')
        if "api" in step_lower and "contains" in step_lower:
            return py('''step_api_contains():
    assert field in response.body ''')

    return None


def render_step_definitions(feature_name: str, scenarios: list[dict]) -> str:
    """Render Ruby step definitions for all scenarios in a feature."""
    lines = []

    lines.append(f"# frozen_string_literal: true")
    lines.append(f"# Step definitions for: {feature_name}")
    lines.append(f"# Generated from LME Matching Rules BDD pipeline")
    lines.append("")

    seen_patterns: set[str] = set()

    for scenario in scenarios:
        given_steps = scenario.get("given", [])
        when_steps = scenario.get("when", [])
        then_steps = scenario.get("then", [])

        for i, step in enumerate(given_steps):
            pattern = extract_step_pattern(step)
            if pattern not in seen_patterns:
                seen_patterns.add(pattern)
                lines.append(generate_step_definition(step, "given", i, feature_name))
                lines.append("")

        for i, step in enumerate(when_steps):
            pattern = extract_step_pattern(step)
            if pattern not in seen_patterns:
                seen_patterns.add(pattern)
                lines.append(generate_step_definition(step, "when", i, feature_name))
                lines.append("")

        for i, step in enumerate(then_steps):
            pattern = extract_step_pattern(step)
            if pattern not in seen_patterns:
                seen_patterns.add(pattern)
                lines.append(generate_step_definition(step, "then", i, feature_name))
                lines.append("")

    return "\n".join(lines)


def write_feature_files(results: list[dict], output_dir: Path) -> list[Path]:
    """Write feature files to disk."""
    features_dir = output_dir / "features" / "matching_rules"
    features_dir.mkdir(parents=True, exist_ok=True)

    written_files: list[Path] = []

    for item in results:
        semantic_rule_id = item.get("semantic_rule_id", "unknown")
        feature_title = item.get("feature", "Unnamed Feature")
        scenarios = item.get("scenarios", [])

        # Use first scenario's intent as description if available
        intent = ""
        if scenarios and len(scenarios) > 0:
            intent = scenarios[0].get("intent", "")

        filename = f"{semantic_rule_id}_{sanitize_filename(feature_title)}.feature"
        filepath = features_dir / filename

        content = render_feature_file(semantic_rule_id, feature_title, scenarios, intent)
        filepath.write_text(content, encoding="utf-8")
        written_files.append(filepath)

    return written_files


def write_step_definitions(results: list[dict], output_dir: Path) -> Path:
    """Write consolidated Ruby step definitions to disk."""
    steps_dir = output_dir / "features" / "step_definitions"
    steps_dir.mkdir(parents=True, exist_ok=True)

    filepath = steps_dir / "matching_rules_steps.rb"

    all_lines: list[str] = []
    seen_patterns: set[str] = set()

    for item in results:
        feature_name = item.get("feature", "Unnamed Feature")
        scenarios = item.get("scenarios", [])

        for scenario in scenarios:
            given_steps = scenario.get("given", [])
            when_steps = scenario.get("when", [])
            then_steps = scenario.get("then", [])

            for step in given_steps:
                pattern = extract_step_pattern(step)
                if pattern not in seen_patterns:
                    seen_patterns.add(pattern)
                    all_lines.append(generate_step_definition(step, "given", 0, feature_name))
                    all_lines.append("")

            for step in when_steps:
                pattern = extract_step_pattern(step)
                if pattern not in seen_patterns:
                    seen_patterns.add(pattern)
                    all_lines.append(generate_step_definition(step, "when", 0, feature_name))
                    all_lines.append("")

            for step in then_steps:
                pattern = extract_step_pattern(step)
                if pattern not in seen_patterns:
                    seen_patterns.add(pattern)
                    all_lines.append(generate_step_definition(step, "then", 0, feature_name))
                    all_lines.append("")

    content = "\n".join(all_lines)
    filepath.write_text(content, encoding="utf-8")

    return filepath


def _extract_scenario_titles_from_feature_file(feature_file: str) -> dict[str, str]:
    """Extract scenario_id -> title mapping from feature_file text.

    Format expected:
      @medium @positive @SR-MR-001-01
      Scenario: Capitalised terms resolve to LME Rulebook definitions
        TC-SR-MR-001-01-positive-01
    """
    titles = {}
    lines = feature_file.split("\n")
    current_title = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("Scenario:"):
            current_title = stripped[len("Scenario:"):].strip()
        elif stripped.startswith("TC-SR-") and current_title:
            # This is the scenario_id line after the Scenario title
            scenario_id = stripped.strip()
            titles[scenario_id] = current_title
            current_title = None
    return titles


def write_feature_files_from_llm(bdd_results: list[dict], output_dir: Path) -> list[Path]:
    """DEPRECATED: Use render_gherkin_from_normalized_bdd instead.

    Write feature files from LLM-generated content.

    Extracts Feature header and renders scenarios from structured data.
    """
    return render_gherkin_from_normalized_bdd(bdd_results, output_dir)


def write_step_definitions_from_llm(bdd_results: list[dict], output_dir: Path) -> list[Path]:
    """DEPRECATED: Use render_steps_from_normalized_bdd instead.

    Write step definitions directly from LLM-generated content.
    Returns a list of per-feature step definition file paths.
    """
    return render_steps_from_normalized_bdd(bdd_results, output_dir)


def render_gherkin_from_normalized_bdd(bdd_results: list[dict], output_dir: Path) -> list[Path]:
    """Render Gherkin .feature files from normalized BDD output.

    Consumes normalized BDD results (produced by run_bdd_pipeline) and
    renders them into Gherkin .feature files.
    """
    features_dir = output_dir / "features" / "matching_rules"
    features_dir.mkdir(parents=True, exist_ok=True)

    written_files: list[Path] = []

    for item in bdd_results:
        semantic_rule_id = item.get("semantic_rule_id", "unknown")
        feature_title = item.get("feature_title", "Unnamed Feature")
        feature_desc = item.get("feature_description", "")
        scenarios = item.get("scenarios", [])
        paragraph_ids = item.get("paragraph_ids", [])

        # Build feature header
        lines = []
        lines.append(f"Feature: {feature_title}")
        lines.append(f"  {semantic_rule_id}")
        if paragraph_ids:
            lines.append(f"  # paragraph_ids: {', '.join(paragraph_ids)}")
        if feature_desc:
            lines.append(f"  {feature_desc}")
        lines.append("")

        # Render each scenario
        for scenario in scenarios:
            scenario_id = scenario.get("scenario_id", "unknown")
            title = scenario.get("title", "Unnamed scenario")
            case_type = scenario.get("case_type", "positive")
            priority = scenario.get("priority", "medium")

            tags = build_tags(case_type, priority)
            lines.append(f"  {' '.join(tags)}  # {scenario_id}")
            lines.append(f"  Scenario: {title}")

            # Given steps
            given_steps = scenario.get("given_steps", [])
            for i, step in enumerate(given_steps):
                step_text = step.get("step_text", "") if isinstance(step, dict) else step
                prefix = "Given" if i == 0 else "And"
                lines.append(f"    {prefix} {step_text}")

            # When steps
            when_steps = scenario.get("when_steps", [])
            for i, step in enumerate(when_steps):
                step_text = step.get("step_text", "") if isinstance(step, dict) else step
                prefix = "When" if i == 0 else "And"
                lines.append(f"    {prefix} {step_text}")

            # Then steps
            then_steps = scenario.get("then_steps", [])
            for i, step in enumerate(then_steps):
                step_text = step.get("step_text", "") if isinstance(step, dict) else step
                prefix = "Then" if i == 0 else "And"
                lines.append(f"    {prefix} {step_text}")

            lines.append("")

        content = "\n".join(lines)
        filename = f"{semantic_rule_id}_{sanitize_filename(feature_title)}.feature"
        filepath = features_dir / filename
        filepath.write_text(content, encoding="utf-8")
        written_files.append(filepath)

    return written_files


def apply_human_step_edits(
    bdd_results: list[dict],
    human_scripts_edits_path: Path,
) -> list[dict]:
    """Apply human step edits (Scripts tab and BDD tab) to normalized BDD results.

    Supports two edit formats:
    - Scripts tab (no scenario_id): updates ``step_definitions[step_type][step_index]``
    - BDD tab (scenario_id present): updates BOTH scenario step arrays
      (``scenarios[i][step_type_steps][step_index]``) AND ``step_definitions``

    Gap steps (is_gap=True) are appended as new entries in step_definitions.

    Modifies bdd_results in-place and returns it.
    """
    import json as _json

    if not human_scripts_edits_path:
        return bdd_results
    edits_path = Path(human_scripts_edits_path)
    if edits_path.name in ("", ".", ".."):
        return bdd_results
    if not edits_path.is_file():
        return bdd_results

    with edits_path.open(encoding="utf-8") as f:
        payload = _json.load(f)

    edits: list[dict] = payload.get("edits", [])
    if not edits:
        return bdd_results

    for edit in edits:
        step_type = edit.get("step_type", "")
        step_index = edit.get("step_index")
        gap_index = edit.get("gap_index")
        step_text = edit.get("step_text", "").strip()
        is_gap = edit.get("is_gap", False)
        scenario_id = edit.get("scenario_id")  # Present for BDD tab edits

        if not step_text:
            continue

        # Extract pattern from the (possibly new) step text
        step_pattern = extract_step_pattern(step_text)

        # Generate code: prefer template, fall back to implementation generator
        template_code = map_step_to_template(step_text, step_type, require_exact=False)
        if template_code:
            code = template_code
        else:
            generated = _generate_python_implementation(step_text, step_type, step_pattern, step_text.capitalize())
            code = generated or ""

        if is_gap:
            # Append gap step as a new entry in step_definitions
            for item in bdd_results:
                step_defs = item.setdefault("step_definitions", {})
                type_steps = step_defs.setdefault(step_type, [])
                type_steps.append({
                    "step_text": step_text,
                    "step_pattern": step_pattern,
                    "code": code,
                    "human_edited": True,
                    "is_gap": True,
                    "gap_index": gap_index,
                })
        elif scenario_id is not None:
            # BDD tab edit: update scenario step text AND step_definitions
            for item in bdd_results:
                for scenario in item.get("scenarios", []):
                    if scenario.get("scenario_id") != scenario_id:
                        continue
                    steps_key = f"{step_type}_steps"
                    type_steps = scenario.get(steps_key, [])
                    if step_index is not None and 0 <= step_index < len(type_steps):
                        # Update scenario step text and pattern
                        type_steps[step_index] = {
                            **type_steps[step_index],
                            "step_text": step_text,
                            "step_pattern": step_pattern,
                        }
                        # Also update the corresponding step_definitions entry
                        step_defs = item.setdefault("step_definitions", {})
                        def_steps = step_defs.get(step_type, [])
                        if 0 <= step_index < len(def_steps):
                            def_steps[step_index] = {
                                **def_steps[step_index],
                                "step_text": step_text,
                                "step_pattern": step_pattern,
                                "code": code,
                                "human_edited": True,
                            }
                        break
                else:
                    continue
                break
        else:
            # Scripts tab edit (no scenario_id): update step_definitions only
            for item in bdd_results:
                step_defs = item.get("step_definitions", {})
                type_steps = step_defs.get(step_type, [])
                if step_index is not None and 0 <= step_index < len(type_steps):
                    type_steps[step_index] = {
                        **type_steps[step_index],
                        "step_text": step_text,
                        "step_pattern": step_pattern,
                        "code": code,
                        "human_edited": True,
                    }
                    break

    return bdd_results


def _canonicalize_step_code(step_text: str, step_type: str, idx: int, feature_name: str, human_edited: bool, existing_code: str) -> str:
    """Resolve step code: prefer STEP_LIBRARY, then existing_code, then generator."""
    from lme_testing.step_library import STEP_LIBRARY

    if step_text in STEP_LIBRARY:
        return STEP_LIBRARY[step_text].render()
    if existing_code:
        return existing_code
    if human_edited:
        return generate_step_definition(step_text, step_type, idx, feature_name, human_edited=True)
    return ""


def _render_step_with_context(step_text: str, step_type: str, step_pattern: str) -> str:
    """Render a single step definition using context for state sharing.

    Uses behave-style context object instead of module-level globals.
    Shared objects are stored as context attributes (context.member, context.trade, etc.).
    """
    keyword = step_type.lower()
    safe_name = re.sub(r"[^\w]", "_", step_pattern.lower())[:50].strip("_") or f"step_{keyword}_{abs(hash(step_text)) % 1000}"

    # Escape single quotes in step text for Python string literal
    escaped = step_text.replace("\\", "\\\\").replace("'", "\\'")
    return f'''@{keyword}("{escaped}")
def {safe_name}(context):
    # TODO: implement step: {step_text}
    pass'''


def render_environment_file(output_dir: Path) -> Path:
    """Write behave environment.py with before/after scenario hooks.

    Provides shared context setup/teardown and LME client initialization.
    """
    env_dir = output_dir / "features"
    env_dir.mkdir(parents=True, exist_ok=True)

    content = '''"""Behave environment hooks for LME Matching Rules BDD suite."""
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
'''

    filepath = env_dir / "environment.py"
    filepath.write_text(content, encoding="utf-8")
    return filepath


def render_steps_from_normalized_bdd(
    bdd_results: list[dict],
    output_dir: Path,
    human_scripts_edits_path: Path | None = None,
) -> list[Path]:
    """Render Python step definitions from normalized BDD output.

    Produces behave-style grouped step files:
    - ``features/step_definitions/{semantic_rule_id}_steps.py`` — one file per feature
    - ``features/environment.py`` — behave hooks for context setup

    Each step file uses ``context`` to share state (context.member, context.trade, etc.)
    instead of module-level global variables.

    If ``human_scripts_edits_path`` is provided, applies human step edits
    (from the Scripts tab) before rendering.
    """
    if human_scripts_edits_path:
        bdd_results = apply_human_step_edits(bdd_results, human_scripts_edits_path)

    steps_dir = output_dir / "features" / "step_definitions"
    steps_dir.mkdir(parents=True, exist_ok=True)

    # Write environment.py hooks
    env_path = render_environment_file(output_dir)

    written_files: list[Path] = []

    for item in bdd_results:
        semantic_rule_id = item.get("semantic_rule_id", "unknown")
        feature_title = item.get("feature_title", "unnamed")
        step_defs = item.get("step_definitions", {})

        # Deduplicate steps within this feature
        seen: set[str] = set()
        lines: list[str] = []

        header = f'''"""Step definitions for: {feature_title} ({semantic_rule_id})

Generated from LME BDD Pipeline (Normalized BDD).
WARNING: Auto-generated — DO NOT EDIT MANUALLY.

Behave framework: steps use ``context`` for state sharing.
Shared objects: context.session, context.member, context.trade,
                context.order, context.request, context.deadline,
                context.contact_response, context.validation_result
"""
from behave import given, when, then


'''
        lines.append(header)

        for step_type in ("given", "when", "then"):
            steps = step_defs.get(step_type, [])
            for idx, step in enumerate(steps):
                step_dict = step if isinstance(step, dict) else {}
                step_text = step_dict.get("step_text", "") if isinstance(step, dict) else ""
                step_pattern = step_dict.get("step_pattern", step_text) if isinstance(step, dict) else step
                code = step_dict.get("code", "") if isinstance(step, dict) else ""
                human_edited = step_dict.get("human_edited", False)

                if not step_pattern or step_pattern in seen:
                    continue
                seen.add(step_pattern)

                resolved_code = _canonicalize_step_code(
                    step_text, step_type, idx, feature_title, human_edited, code
                )

                if resolved_code:
                    # Convert module-level step to context-aware version
                    context_code = _convert_to_context_style(resolved_code, step_text, step_type)
                    lines.append(context_code)
                    lines.append("")
                else:
                    # Fallback: generate context-aware pending stub
                    stub = _render_step_with_context(step_text, step_type, step_pattern)
                    lines.append(stub)
                    lines.append("")

        # Write per-feature step file
        safe_id = re.sub(r"[^\w]", "_", semantic_rule_id)
        filepath = steps_dir / f"{safe_id}_steps.py"
        filepath.write_text("\n".join(lines), encoding="utf-8")
        written_files.append(filepath)

    return written_files


def _convert_to_context_style(code: str, step_text: str, step_type: str) -> str:
    """Convert a module-level step definition to behave context style.

    Replaces bare ``variable = ...`` assignments with ``context.variable = ...``,
    replaces bare ``variable.name`` attribute accesses with ``context.variable.name``,
    bare ``variable`` function-call arguments with ``context.variable``,
    and adds ``context`` parameter to the function.
    """
    import re as _re

    # If already has (context) parameter, return as-is
    if "(context)" in code:
        return code

    # Strip the decorator and function signature
    decorator_match = _re.search(r"^(@\w+\(.*?\)\n)", code)
    decorator = decorator_match.group(1) if decorator_match else f"@{step_type.lower()}('{_escape_py_str(step_text)}')\n"

    # Extract function body
    body_match = _re.search(r"^@\w+\(.*?\)\ndef \w+\(.*?\):\n(.*)$", code, _re.DOTALL)
    if body_match:
        body = body_match.group(1)
    else:
        return code.replace("def ", "def ", 1)

    # Known LME object names
    lme_objects = [
        "member", "session", "trade", "order", "request", "deadline",
        "contact_response", "validation_result", "trade_params",
        "trade_submission", "resubmission_response", "response",
        "agreement", "agreements", "env", "rules", "adoption_status",
        "contact_status",
    ]

    # Step 1: Bare assignment targets at line start.
    # Matches "    member = ..." → "    context.member = ..."
    # Captures the "= ..." part so it's preserved after replacement.
    for obj in lme_objects:
        body = _re.sub(rf"^(\s*)\b{obj}\b(\s*=\s*)", rf"\1context.{obj}\2", body, flags=_re.MULTILINE)

    # Step 2: Bare attribute accesses (.obj. or .obj at EOL), not already context.
    # Matches ".validation_result." or ".validation_result" at end of line
    for obj in lme_objects:
        body = _re.sub(rf"(?<!\bcontext\.)\b{obj}\b(?=\s*\.)", rf"context.{obj}", body)
        body = _re.sub(rf"(?<!\bcontext\.)\b{obj}\b(\s*$)", rf"context.{obj}\1", body)

    # Step 3: Bare return statements (return obj at line start), not already context.
    # Must have word boundary before and nothing after but whitespace.
    for obj in lme_objects:
        body = _re.sub(rf"^(\s*)\breturn\s+{obj}\b\s*$", rf"\1return context.{obj}", body, flags=_re.MULTILINE)

    # Step 4: Bare variables used as function arguments.
    # Matches "func(arg1, member, arg3)" — member is not at line start and
    # is followed by comma or close-paren, not an equals sign.
    # Negative lookbehind ensures not already context.member.
    for obj in lme_objects:
        body = _re.sub(rf"(?<!\bcontext\.)\b{obj}\b(?=\s*[,)])", rf"context.{obj}", body)

    func_name_match = _re.search(r"def (\w+)\(", code)
    func_name = func_name_match.group(1) if func_name_match else "unnamed_step"

    return f"{decorator}def {func_name}(context):\n{body}"


def run_bdd_export(maker_cases_path: Path, output_dir: Path) -> dict:
    """Run full BDD export: feature files + step definitions.

    This is a template-based export that doesn't call LLM.
    For LLM-refined output, use run_bdd_pipeline instead.
    """
    from .storage import ensure_dir, load_jsonl

    maker_records = load_jsonl(maker_cases_path)
    output_dir = ensure_dir(output_dir)

    # Transform maker records to BDD format
    results: list[dict] = []
    for record in maker_records:
        results.append({
            "semantic_rule_id": record.get("semantic_rule_id", "unknown"),
            "feature": record.get("feature", "Unnamed Feature"),
            "scenarios": record.get("scenarios", []),
        })

    # Write outputs
    feature_files = write_feature_files(results, output_dir)
    step_file = write_step_definitions(results, output_dir)

    return {
        "output_dir": str(output_dir),
        "feature_files_count": len(feature_files),
        "feature_files": [str(f) for f in feature_files],
        "step_definitions_file": str(step_file),
    }
