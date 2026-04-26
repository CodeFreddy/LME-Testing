from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

from lme_testing.config import ProjectConfig, ProviderConfig, RoleDefaults
from lme_testing.workflow_session import choose_start_step, discover_workflow_artifacts, start_workflow_session


WORK_TMP = Path('.tmp_workflow_session')


def make_config() -> ProjectConfig:
    provider = ProviderConfig(
        name='shared',
        provider_type='openai_compatible',
        model='demo-model',
        base_url='https://example.com/v1',
        api_key='secret',
    )
    return ProjectConfig(
        providers={'shared': provider},
        roles={'maker': 'shared', 'checker': 'shared'},
        output_root=Path('runs'),
        maker_defaults=RoleDefaults(),
        checker_defaults=RoleDefaults(),
    )


class WorkflowSessionTests(unittest.TestCase):
    def setUp(self) -> None:
        WORK_TMP.mkdir(exist_ok=True)

    def tearDown(self) -> None:
        if WORK_TMP.exists():
            shutil.rmtree(WORK_TMP)

    def test_choose_start_step_honors_requested_value(self) -> None:
        artifacts_dir = WORK_TMP / 'artifacts'
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        (artifacts_dir / 'atomic_rules.json').write_text('[]', encoding='utf-8')
        (artifacts_dir / 'semantic_rules.json').write_text('[]', encoding='utf-8')
        maker_cases = WORK_TMP / 'maker_cases.jsonl'
        maker_cases.write_text('', encoding='utf-8')
        checker_reviews = WORK_TMP / 'checker_reviews.jsonl'
        checker_reviews.write_text('', encoding='utf-8')
        summary = WORK_TMP / 'summary.json'
        summary.write_text('{}', encoding='utf-8')
        coverage = WORK_TMP / 'coverage.json'
        coverage.write_text('{}', encoding='utf-8')
        artifacts = discover_workflow_artifacts(
            repo_root=WORK_TMP,
            source_path=WORK_TMP / 'source.md',
            artifacts_dir=artifacts_dir,
            maker_cases_path=maker_cases,
            maker_summary_path=summary,
            checker_reviews_path=checker_reviews,
            checker_summary_path=summary,
            coverage_report_path=coverage,
        )
        self.assertEqual(choose_start_step(artifacts, 'review'), 'review')

    def test_start_workflow_session_from_review_uses_existing_artifacts(self) -> None:
        source = WORK_TMP / 'source.md'
        source.write_text('demo', encoding='utf-8')
        artifacts_dir = WORK_TMP / 'artifacts'
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        (artifacts_dir / 'atomic_rules.json').write_text('[]', encoding='utf-8')
        semantic_rules = [{'semantic_rule_id': 'SR-1', 'classification': {'rule_type': 'permission', 'coverage_eligible': True}, 'source': {'atomic_rule_ids': ['AR-1']}, 'evidence': [{'atomic_rule_id': 'AR-1', 'page': 1, 'quote': 'q'}]}]
        (artifacts_dir / 'semantic_rules.json').write_text(json.dumps(semantic_rules, ensure_ascii=False), encoding='utf-8')
        maker_cases = WORK_TMP / 'maker_cases.jsonl'
        checker_reviews = WORK_TMP / 'checker_reviews.jsonl'
        maker_summary = WORK_TMP / 'maker_summary.json'
        checker_summary = WORK_TMP / 'checker_summary.json'
        coverage_report = WORK_TMP / 'coverage_report.json'
        maker_cases.write_text(json.dumps({'run_id': 'r1', 'semantic_rule_id': 'SR-1', 'requirement_ids': ['AR-1'], 'feature': 'F', 'scenarios': [{'scenario_id': 'TC-1', 'title': 'T', 'intent': 'I', 'priority': 'high', 'case_type': 'positive', 'given': [], 'when': [], 'then': [], 'assumptions': [], 'evidence': [{'atomic_rule_id': 'AR-1', 'page': 1, 'quote': 'q'}]}]}) + '\n', encoding='utf-8')
        checker_reviews.write_text(json.dumps({'case_id': 'TC-1', 'semantic_rule_id': 'SR-1', 'overall_status': 'pass', 'scores': {}, 'coverage_assessment': {'status': 'covered', 'reason': 'ok', 'missing_aspects': []}, 'checker_blocking': False, 'findings': []}) + '\n', encoding='utf-8')
        maker_summary.write_text(json.dumps({'run_id': 'r1', 'processed_rule_count': 1, 'scenario_count': 1, 'results_path': str(maker_cases)}, ensure_ascii=False), encoding='utf-8')
        checker_summary.write_text(json.dumps({'run_id': 'r2', 'review_count': 1, 'results_path': str(checker_reviews), 'coverage_report_path': str(coverage_report)}, ensure_ascii=False), encoding='utf-8')
        coverage_report.write_text(json.dumps({'total_requirements': 1, 'fully_covered': 1, 'partially_covered': 0, 'uncovered': 0, 'status_by_rule': {'SR-1': {'rule_type': 'permission', 'rule_coverage_status': 'fully_covered', 'rule_pass_status': 'pass', 'required_case_types': ['positive'], 'present_case_types': ['positive'], 'accepted_case_types': ['positive'], 'missing_case_types': []}}}, ensure_ascii=False), encoding='utf-8')
        artifacts = discover_workflow_artifacts(
            repo_root=WORK_TMP,
            source_path=source,
            artifacts_dir=artifacts_dir,
            maker_cases_path=maker_cases,
            maker_summary_path=maker_summary,
            checker_reviews_path=checker_reviews,
            checker_summary_path=checker_summary,
            coverage_report_path=coverage_report,
        )
        server, url, manager = start_workflow_session(
            config=make_config(),
            repo_root=Path.cwd(),
            artifacts=artifacts,
            output_root=WORK_TMP / 'sessions',
            host='127.0.0.1',
            port=0,
            start_step='review',
            maker_batch_size=1,
            checker_batch_size=1,
            write_page_text=False,
        )
        try:
            payload = manager.session_payload()
            self.assertEqual(payload['current_iteration'], 0)
            self.assertTrue(payload['metadata']['current_report_path'])
            self.assertTrue(url.startswith('http://127.0.0.1:'))
        finally:
            server.server_close()


if __name__ == '__main__':
    unittest.main()

