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


def map_step_to_template(step: str, step_type: str) -> str | None:
    """Map a step to a known template if available."""
    step_lower = step.lower()

    for key, template in TEMPLATE_REGISTRY.items():
        pattern_field = f"{step_type}_pattern"
        if pattern_field in template:
            if template[pattern_field].lower() in step_lower or step_lower in template[pattern_field].lower():
                return template.get(f"{step_type}_code")

    return None


def generate_step_definition(step: str, step_type: str, step_index: int, feature_name: str) -> str:
    """Generate Ruby step definition code for a given step."""
    # Try to use template
    template_code = map_step_to_template(step, step_type)
    if template_code:
        return template_code

    # Generate generic step definition
    pattern = extract_step_pattern(step)
    step_text = step.capitalize()

    if step_type == "given":
        return f'''Given(/^{pattern}$/) do
  # TODO: Implement: {step_text}
  pending "Step not implemented: {step}"
end'''
    elif step_type == "when":
        return f'''When(/^{pattern}$/) do
  # TODO: Implement: {step_text}
  pending "Step not implemented: {step}"
end'''
    else:  # then
        return f'''Then(/^{pattern}$/) do
  # TODO: Implement: {step_text}
  pending "Step not implemented: {step}"
end'''


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
    """Write feature files from LLM-generated content.

    Extracts Feature header and renders scenarios from structured data.
    """
    features_dir = output_dir / "features" / "matching_rules"
    features_dir.mkdir(parents=True, exist_ok=True)

    written_files: list[Path] = []

    for item in bdd_results:
        semantic_rule_id = item.get("semantic_rule_id", "unknown")
        feature_name = item.get("feature_name", "unnamed_feature")
        scenarios = item.get("scenarios", [])

        # Build feature header from feature_file if available
        feature_file = item.get("feature_file", "")
        if feature_file:
            # Extract titles from feature_file
            scenario_titles = _extract_scenario_titles_from_feature_file(feature_file)

            # Extract lines until we hit a Scenario or tag block
            lines = feature_file.split("\n")
            header_lines = []
            for line in lines:
                stripped = line.strip()
                # Stop at first Scenario or @tag (which precedes scenario)
                if stripped.startswith("Scenario:") or (stripped.startswith("@") and header_lines):
                    break
                header_lines.append(line)
            feature_header = "\n".join(header_lines).rstrip()
        else:
            scenario_titles = {}
            feature_header = f"Feature: {feature_name}\n  {semantic_rule_id}"

        # Inject titles into scenarios before rendering
        for scenario in scenarios:
            scenario_id = scenario.get("scenario_id", "")
            if scenario_id in scenario_titles and not scenario.get("title"):
                scenario["title"] = scenario_titles[scenario_id]

        # Render scenarios from structured data
        output_lines = [feature_header, ""]

        for scenario in scenarios:
            output_lines.append(render_scenario(scenario, semantic_rule_id))
            output_lines.append("")

        content = "\n".join(output_lines)

        filename = f"{semantic_rule_id}_{sanitize_filename(feature_name)}.feature"
        filepath = features_dir / filename
        filepath.write_text(content, encoding="utf-8")
        written_files.append(filepath)

    return written_files


def write_step_definitions_from_llm(bdd_results: list[dict], output_dir: Path) -> Path:
    """Write step definitions directly from LLM-generated content.

    Uses the step_definitions field from LLM output directly.
    """
    steps_dir = output_dir / "features" / "step_definitions"
    steps_dir.mkdir(parents=True, exist_ok=True)

    filepath = steps_dir / "matching_rules_steps.rb"

    all_lines: list[str] = []
    seen_patterns: set[str] = set()

    all_lines.append("# frozen_string_literal: true")
    all_lines.append("# Step definitions - Generated from LME BDD Pipeline")
    all_lines.append("# WARNING: Auto-generated - DO NOT EDIT MANUALLY")
    all_lines.append("")

    for item in bdd_results:
        feature_name = item.get("feature_name", "unnamed")
        step_defs = item.get("step_definitions", {})

        for step_type in ("given", "when", "then"):
            steps = step_defs.get(step_type, [])
            for step in steps:
                pattern = step.get("pattern", "")
                code = step.get("code", "")

                # Avoid duplicates by pattern
                if pattern and pattern not in seen_patterns:
                    seen_patterns.add(pattern)
                    if code:
                        all_lines.append(code)
                        all_lines.append("")

    content = "\n".join(all_lines)
    filepath.write_text(content, encoding="utf-8")

    return filepath


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
