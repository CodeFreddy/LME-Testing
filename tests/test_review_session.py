from __future__ import annotations

import json
import shutil
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from lme_testing.config import ProjectConfig, ProviderConfig, RoleDefaults
from lme_testing.review_session import ReviewSessionManager, _render_review_session_shell, _validate_script_ai_payload
from lme_testing.schemas import SchemaError
from lme_testing.step_registry import (
    compute_step_matches,
    extract_steps_from_normalized_bdd,
    extract_steps_from_python_step_defs,
    render_step_visibility_report,
)


WORK_TMP = Path('.tmp_review_session')


class FakeProvider:
    def __init__(self, responses: list[str]):
        self.responses = responses
        self.index = 0

    def generate(self, system_prompt: str, user_prompt: str):
        payload = json.loads(self.responses[self.index])
        self.index += 1
        return type('Response', (), {'content': json.dumps(payload, ensure_ascii=False), 'raw_response': payload})()


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


class ReviewSessionTests(unittest.TestCase):
    def setUp(self) -> None:
        WORK_TMP.mkdir(exist_ok=True)

    def tearDown(self) -> None:
        if WORK_TMP.exists():
            shutil.rmtree(WORK_TMP)

    def test_save_reviews_writes_snapshot_and_latest(self) -> None:
        manager = self._build_manager()
        payload = self._payload('rewrite', 'approve')
        result = manager.save_reviews(payload)
        self.assertTrue(Path(result['saved_review_path']).exists())
        self.assertTrue(Path(result['latest_review_path']).exists())

    def test_save_reviews_normalizes_legacy_review_fields(self) -> None:
        manager = self._build_manager()
        payload = self._payload('reject', 'approved')
        result = manager.save_reviews(payload)

        latest_payload = json.loads(Path(result['latest_review_path']).read_text(encoding='utf-8'))

        self.assertEqual([item['review_decision'] for item in latest_payload['reviews']], ['rewrite', 'approve'])
        self.assertNotIn('block_recommendation_review', latest_payload['reviews'][0])
        self.assertNotIn('block_recommendation_review', latest_payload['reviews'][1])

    def test_save_reviews_treats_pending_comment_as_rewrite(self) -> None:
        manager = self._build_manager()
        payload = self._payload('pending', 'approve')
        payload['reviews'][0]['human_comment'] = '  please rewrite this case with clearer inputs  '
        result = manager.save_reviews(payload)

        latest_payload = json.loads(Path(result['latest_review_path']).read_text(encoding='utf-8'))

        self.assertEqual(latest_payload['reviews'][0]['review_decision'], 'rewrite')
        self.assertEqual(latest_payload['reviews'][0]['human_comment'], '  please rewrite this case with clearer inputs  ')

    def test_review_session_shell_uses_three_state_decision_ui(self) -> None:
        html = _render_review_session_shell()

        self.assertIn('<option value="pending"', html)
        self.assertIn('<option value="approve"', html)
        self.assertIn('<option value="rewrite"', html)
        self.assertNotIn('<option value="reject"', html)
        self.assertNotIn('Block Recommendation Review', html)
        self.assertIn('View Changes', html)
        self.assertIn('PHASE_PROGRESS', html)
        self.assertNotIn('id="overallFilter"', html)
        self.assertNotIn('<th>Overall</th>', html)
        self.assertIn('正在 checker 复检', html)
        self.assertNotIn('rewrite_summary', html)
        self.assertNotIn('checker_summary', html)
        self.assertNotIn('Latest review path', html)

    def test_audit_trail_records_human_checker_divergence_after_normalization(self) -> None:
        manager = self._build_manager()
        manager.save_reviews(self._payload('reject', 'approve'))

        trail = manager.rebuild_audit_trail()

        self.assertEqual(trail['divergent_count'], 1)
        self.assertTrue(Path(trail['audit_trail_path']).exists())

    def test_submit_reviews_advances_iteration_and_generates_report(self) -> None:
        manager = self._build_manager()
        payload = self._payload('rewrite', 'approve')
        rewrite_response = json.dumps(
            {
                'results': [
                    {
                        'semantic_rule_id': 'SR-1',
                        'requirement_ids': ['AR-1'],
                        'feature': 'Feature rewritten',
                        'scenarios': [
                            {
                                'scenario_id': 'TC-1-rewritten',
                                'title': 'Rewrite',
                                'intent': 'rewrite',
                                'priority': 'high',
                                'case_type': 'positive',
                                'given': ['g'],
                                'when': ['w'],
                                'then': ['t'],
                                'assumptions': [],
                                'evidence': [{'atomic_rule_id': 'AR-1', 'page': 1, 'quote': 'q'}],
                            }
                        ],
                    }
                ]
            }
        )
        checker_response = json.dumps(
            {
                'results': [
                    {
                        'case_id': 'TC-1-rewritten',
                        'semantic_rule_id': 'SR-1',
                        'overall_status': 'pass',
                        'scores': {'evidence_consistency': 5, 'requirement_coverage': 5, 'test_design_quality': 5, 'non_hallucination': 5},
                        'case_type': 'positive',
                        'case_type_accepted': True,
                        'coverage_relevance': 'direct',
                        'blocking_findings_count': 0,
                        'is_blocking': False,
                        'blocking_category': 'none',
                        'blocking_reason': '',
                        'checker_confidence': 0.95,
                        'findings': [],
                        'coverage_assessment': {'status': 'covered', 'reason': 'ok', 'missing_aspects': []},
                    },
                    {
                        'case_id': 'TC-2',
                        'semantic_rule_id': 'SR-2',
                        'overall_status': 'pass',
                        'scores': {'evidence_consistency': 5, 'requirement_coverage': 5, 'test_design_quality': 5, 'non_hallucination': 5},
                        'case_type': 'positive',
                        'case_type_accepted': True,
                        'coverage_relevance': 'direct',
                        'blocking_findings_count': 0,
                        'is_blocking': False,
                        'blocking_category': 'none',
                        'blocking_reason': '',
                        'checker_confidence': 0.95,
                        'findings': [],
                        'coverage_assessment': {'status': 'covered', 'reason': 'ok', 'missing_aspects': []},
                    },
                ]
            }
        )
        with patch('lme_testing.pipelines.build_provider', return_value=FakeProvider([rewrite_response, checker_response])):
            submit_result = manager.submit_reviews(payload)
            for _ in range(50):
                status = manager.job_status(submit_result['job_id'])
                if status['status'] in {'succeeded', 'failed'}:
                    break
                time.sleep(0.1)
        self.assertEqual(status['status'], 'succeeded')
        session = manager.session_payload()
        self.assertEqual(session['current_iteration'], 1)
        self.assertTrue(session['metadata']['current_report_path'])
        self.assertIn('report_html', status['result']['links'])
        self.assertEqual(status['result']['history_iteration'], 0)
        self.assertIn('case_compare_html', status['result']['links'])
        self.assertTrue(status['result']['links']['case_compare_html'])
        self.assertEqual(len(session['history']), 1)
        self.assertEqual(session['history'][0]['next_iteration'], 1)
        self.assertTrue(session['history'][0]['compare_path'])
        self.assertTrue(Path(session['history'][0]['compare_path']).exists())

    def test_finalize_locks_session(self) -> None:
        manager = self._build_manager()
        result = manager.finalize_session()
        self.assertEqual(result['status'], 'finalized')
        with self.assertRaises(ValueError):
            manager.save_reviews(self._payload('pending', 'pending'))

    def test_bdd_edits_export_reviewed_bdd_and_refresh_step_registry(self) -> None:
        manager = self._build_manager(include_bdd=True)
        result = manager.save_bdd_edits({
            'edits': [
                {
                    'scenario_id': 'TC-1',
                    'given_steps': [{'step_text': 'business is transacted on the Exchange'}],
                    'when_steps': [],
                    'then_steps': [],
                }
            ]
        })

        reviewed_path = Path(result['reviewed_bdd_path'])
        registry_path = Path(result['refreshed_step_registry_path'])
        self.assertTrue(reviewed_path.exists())
        self.assertTrue(registry_path.exists())
        reviewed = [json.loads(line) for line in reviewed_path.read_text(encoding='utf-8').splitlines() if line.strip()]
        self.assertEqual(
            reviewed[0]['scenarios'][0]['given_steps'][0]['step_text'],
            'business is transacted on the Exchange',
        )
        registry = json.loads(registry_path.read_text(encoding='utf-8'))
        self.assertGreaterEqual(registry['exact_matches'], 1)

    def test_scripts_gap_edit_updates_reviewed_bdd_and_refreshes_matching(self) -> None:
        manager = self._build_manager(include_bdd=True)
        scripts_payload = manager.scripts_payload()
        self.assertEqual(scripts_payload['summary']['unmatched'], 1)

        result = manager.save_scripts_edits({
            'edits': [
                {
                    'is_gap': True,
                    'gap_index': 0,
                    'step_text': 'business is transacted on the Exchange',
                }
            ]
        })

        reviewed_path = Path(result['reviewed_bdd_path'])
        registry_path = Path(result['refreshed_step_registry_path'])
        reviewed = [json.loads(line) for line in reviewed_path.read_text(encoding='utf-8').splitlines() if line.strip()]
        self.assertEqual(
            reviewed[0]['scenarios'][0]['given_steps'][0]['step_text'],
            'business is transacted on the Exchange',
        )
        registry = json.loads(registry_path.read_text(encoding='utf-8'))
        self.assertEqual(registry['unmatched'], 0)
        self.assertGreaterEqual(registry['exact_matches'], 1)

    def test_create_scripts_by_ai_generates_editable_code_for_unmatched_steps(self) -> None:
        manager = self._build_manager(include_bdd=True)
        manager.repo_root = WORK_TMP
        api_dir = WORK_TMP / 'api-endpoint'
        api_dir.mkdir(exist_ok=True)
        (api_dir / 'mock-hkex-api').write_text(
            json.dumps(
                {
                    'title': 'Mock HKEX API',
                    'endpoints': [
                        {
                            'name': 'getInitialMarginRiskParameters',
                            'method': 'GET',
                            'path': '/api/margin/risk-parameters',
                            'description': 'Returns initial margin risk parameters.',
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding='utf-8',
        )
        response_payload = {
            'scripts': [
                {
                    'step_id': 'given:0',
                    'step_type': 'given',
                    'step_text': 'custom unmatched setup',
                    'endpoint_name': 'getInitialMarginRiskParameters',
                    'code': '@given("custom unmatched setup")\ndef step_custom_unmatched_setup(context):\n    context.risk_parameters = context.api.get("/api/margin/risk-parameters")',
                    'notes': 'demo',
                }
            ]
        }
        config = make_config()
        config.providers['scripts_provider'] = ProviderConfig(
            name='scripts_provider',
            provider_type='openai_compatible',
            model='kimi-k2.5',
            base_url='https://example.com/v1',
            api_key='secret',
        )
        config.roles['scripts'] = 'scripts_provider'
        manager.config = config

        with patch('lme_testing.review_session.build_provider', return_value=FakeProvider([json.dumps(response_payload)])):
            job = manager.create_scripts_by_ai({})
            for _ in range(50):
                status = manager.job_status(job['job_id'])
                if status['status'] not in {'queued', 'running'}:
                    break
                time.sleep(0.05)

        status = manager.job_status(job['job_id'])
        self.assertEqual(status['status'], 'succeeded')
        scripts_payload = manager.scripts_payload()
        first_step = scripts_payload['steps_by_type']['given'][0]
        self.assertEqual(first_step['script_source'], 'ai')
        self.assertIn('context.api.get', first_step['code'])
        self.assertTrue(scripts_payload['scripts_ready_to_save'])
        self.assertTrue(scripts_payload['generated_scripts_path'])
        self.assertIn('api-endpoint', scripts_payload['api_catalog_path'])
        edited_code = '@given("custom unmatched setup")\ndef step_custom_unmatched_setup(context):\n    context.edited_by_human = True'
        manager.save_scripts_edits(
            {
                'edits': [
                    {
                        'step_type': 'given',
                        'step_index': 0,
                        'step_text': 'custom unmatched setup',
                        'code': edited_code,
                    }
                ]
            }
        )
        refreshed_payload = manager.scripts_payload()
        refreshed_step = refreshed_payload['steps_by_type']['given'][0]
        self.assertEqual(refreshed_step['script_source'], 'human')
        self.assertEqual(refreshed_step['code'], edited_code)
        self.assertNotIn('context.api.get', refreshed_step['code'])
        with self.assertRaisesRegex(ValueError, 'already been generated'):
            manager.create_scripts_by_ai({})

    def test_create_scripts_by_ai_uses_stub_provider_when_scripts_role_is_absent(self) -> None:
        manager = self._build_manager(include_bdd=True)
        manager.repo_root = Path.cwd()
        provider = ProviderConfig(
            name='stub',
            provider_type='stub',
            model='stub-model',
            base_url='http://stub',
            api_key='stub',
        )
        manager.config = ProjectConfig(
            providers={'stub': provider},
            roles={'maker': 'stub', 'checker': 'stub'},
            output_root=Path('runs'),
            maker_defaults=RoleDefaults(),
            checker_defaults=RoleDefaults(),
        )

        job = manager.create_scripts_by_ai({})
        for _ in range(50):
            status = manager.job_status(job['job_id'])
            if status['status'] not in {'queued', 'running'}:
                break
            time.sleep(0.05)

        self.assertEqual(status['status'], 'succeeded')
        scripts_payload = manager.scripts_payload()
        first_step = scripts_payload['steps_by_type']['given'][0]
        self.assertEqual(first_step['script_source'], 'ai')
        self.assertIn('@given("custom unmatched setup")', first_step['code'])
        self.assertTrue(scripts_payload['scripts_ready_to_save'])

    def test_create_scripts_by_ai_skips_invalid_scripts_without_failing_job(self) -> None:
        manager = self._build_manager(include_bdd=True)
        manager.repo_root = WORK_TMP
        api_dir = WORK_TMP / 'api-endpoint'
        api_dir.mkdir(exist_ok=True)
        (api_dir / 'mock-hkex-api').write_text(
            json.dumps(
                {
                    'title': 'Mock HKEX API',
                    'endpoints': [
                        {
                            'name': 'getMarginCreditBalance',
                            'method': 'GET',
                            'path': '/api/margin/credits/{clearingParticipantId}',
                            'description': 'Returns available margin credit balance.',
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding='utf-8',
        )
        response_payload = {
            'scripts': [
                {
                    'step_id': 'given:0',
                    'step_type': 'given',
                    'step_text': 'custom unmatched setup',
                    'endpoint_name': 'getMarginCreditBalance',
                    'code': '@given("custom unmatched setup")\ndef step_custom_unmatched_setup(context):\n    context.expected_margin_credit = 5000000',
                    'notes': 'context-only setup',
                }
            ]
        }
        config = make_config()
        config.providers['scripts_provider'] = ProviderConfig(
            name='scripts_provider',
            provider_type='openai_compatible',
            model='kimi-k2.5',
            base_url='https://example.com/v1',
            api_key='secret',
        )
        config.roles['scripts'] = 'scripts_provider'
        manager.config = config

        with patch('lme_testing.review_session.build_provider', return_value=FakeProvider([json.dumps(response_payload)])):
            job = manager.create_scripts_by_ai({})
            for _ in range(50):
                status = manager.job_status(job['job_id'])
                if status['status'] not in {'queued', 'running'}:
                    break
                time.sleep(0.05)

        status = manager.job_status(job['job_id'])
        self.assertEqual(status['status'], 'succeeded')
        self.assertEqual(status['result']['skipped_count'], 1)
        scripts_payload = manager.scripts_payload()
        first_step = scripts_payload['steps_by_type']['given'][0]
        self.assertEqual(first_step['validation_status'], 'skipped')
        self.assertIn('context.scenario.skip', first_step['code'])
        self.assertTrue(scripts_payload['scripts_ready_to_save'])

    def test_scripts_ai_validation_requires_selected_endpoint_call(self) -> None:
        payload = {
            'scripts': [
                {
                    'step_id': 'then:0',
                    'step_type': 'then',
                    'step_text': 'Aggregated margin before rounding equals 46,929,904',
                    'endpoint_name': 'calculateAggregatedMarketRiskMargin',
                    'code': '@then("Aggregated margin before rounding equals 46,929,904")\ndef step_verify_aggregated_before_rounding(context):\n    actual = getattr(context, "aggregated_margin_before_rounding", None)\n    assert actual == 46929904',
                    'notes': 'context-only assertion',
                }
            ]
        }

        with self.assertRaisesRegex(SchemaError, 'does not call or assert against a mock HKEX API result'):
            _validate_script_ai_payload(payload, {'then:0'}, {'calculateAggregatedMarketRiskMargin'})

    def test_scripts_ai_validation_allows_then_assertion_against_saved_api_response(self) -> None:
        payload = {
            'scripts': [
                {
                    'step_id': 'then:0',
                    'step_type': 'then',
                    'step_text': 'Aggregated margin before rounding equals 46,929,904',
                    'endpoint_name': 'calculateAggregatedMarketRiskMargin',
                    'code': '@then("Aggregated margin before rounding equals 46,929,904")\ndef step_verify_aggregated_before_rounding(context):\n    actual = context.calculation_response.get("aggregated_margin_before_rounding")\n    assert actual == 46929904',
                    'notes': 'asserts against saved API response',
                }
            ]
        }

        generated = _validate_script_ai_payload(payload, {'then:0'}, {'calculateAggregatedMarketRiskMargin'})

        self.assertEqual(generated[0]['endpoint_name'], 'calculateAggregatedMarketRiskMargin')

    def test_scripts_ai_validation_requires_pending_when_no_endpoint_selected(self) -> None:
        payload = {
            'scripts': [
                {
                    'step_id': 'then:0',
                    'step_type': 'then',
                    'step_text': 'Aggregated margin before rounding equals 46,929,904',
                    'endpoint_name': '',
                    'code': '@then("Aggregated margin before rounding equals 46,929,904")\ndef step_verify_aggregated_before_rounding(context):\n    assert True',
                    'notes': 'context-only assertion',
                }
            ]
        }

        with self.assertRaisesRegex(SchemaError, 'must remain pending with NotImplementedError'):
            _validate_script_ai_payload(payload, {'then:0'}, {'calculateAggregatedMarketRiskMargin'})

    def test_save_scripts_edits_preserves_user_script_code(self) -> None:
        manager = self._build_manager(include_bdd=True)
        code = '@given("custom unmatched setup")\ndef step_custom_unmatched_setup(context):\n    context.value = 1'
        result = manager.save_scripts_edits(
            {
                'edits': [
                    {
                        'step_type': 'given',
                        'step_index': 0,
                        'step_text': 'custom unmatched setup',
                        'code': code,
                    }
                ]
            }
        )
        reviewed = [
            json.loads(line)
            for line in Path(result['reviewed_bdd_path']).read_text(encoding='utf-8').splitlines()
            if line.strip()
        ]
        self.assertEqual(reviewed[0]['step_definitions']['given'][0]['code'], code)
        refreshed_payload = manager.scripts_payload()
        refreshed_step = refreshed_payload['steps_by_type']['given'][0]
        self.assertEqual(refreshed_step['script_source'], 'human')
        self.assertEqual(refreshed_step['code'], code)
        step_files = result.get('step_definitions_files', [])
        self.assertTrue(step_files)
        self.assertIn('context.value = 1', Path(step_files[0]).read_text(encoding='utf-8'))

    def test_scripts_save_preserves_previous_bdd_edits(self) -> None:
        manager = self._build_manager(include_bdd=True)
        manager.save_bdd_edits({
            'edits': [
                {
                    'scenario_id': 'TC-1',
                    'given_steps': [{'step_text': 'Exchange defines matching rules'}],
                    'when_steps': [],
                    'then_steps': [],
                }
            ]
        })

        result = manager.save_scripts_edits({'edits': []})

        latest_payload = json.loads(Path(result['latest_path']).read_text(encoding='utf-8'))
        self.assertEqual(len(latest_payload['edits']), 1)
        self.assertEqual(latest_payload['edits'][0]['scenario_id'], 'TC-1')

        reviewed = [
            json.loads(line)
            for line in Path(result['reviewed_bdd_path']).read_text(encoding='utf-8').splitlines()
            if line.strip()
        ]
        self.assertEqual(
            reviewed[0]['scenarios'][0]['given_steps'][0]['step_text'],
            'Exchange defines matching rules',
        )

    def _payload(self, first_decision: str, second_decision: str) -> dict:
        return {
            'metadata': {},
            'reviews': [
                {
                    'case_id': 'TC-1',
                    'semantic_rule_id': 'SR-1',
                    'review_decision': first_decision,
                    'block_recommendation_review': 'pending_review',
                    'human_comment': '',
                    'issue_types': ['bad_assertion'] if first_decision == 'rewrite' else [],
                },
                {
                    'case_id': 'TC-2',
                    'semantic_rule_id': 'SR-2',
                    'review_decision': second_decision,
                    'block_recommendation_review': 'confirmed' if second_decision == 'approve' else 'not_applicable',
                    'human_comment': '',
                    'issue_types': [],
                },
            ],
        }

    def _build_manager(self, include_bdd: bool = False) -> ReviewSessionManager:
        rules_path = WORK_TMP / 'semantic_rules.json'
        maker_cases_path = WORK_TMP / 'maker_cases.jsonl'
        checker_reviews_path = WORK_TMP / 'checker_reviews.jsonl'
        maker_summary_path = WORK_TMP / 'maker_summary.json'
        checker_summary_path = WORK_TMP / 'checker_summary.json'
        coverage_report_path = WORK_TMP / 'coverage_report.json'
        normalized_bdd_path = WORK_TMP / 'normalized_bdd.jsonl'
        step_registry_path = WORK_TMP / 'step_visibility.json'
        rules = [
            {'semantic_rule_id': 'SR-1', 'source': {'atomic_rule_ids': ['AR-1']}, 'classification': {'rule_type': 'permission', 'coverage_eligible': True}, 'evidence': [{'atomic_rule_id': 'AR-1', 'page': 1, 'quote': 'q'}]},
            {'semantic_rule_id': 'SR-2', 'source': {'atomic_rule_ids': ['AR-2']}, 'classification': {'rule_type': 'permission', 'coverage_eligible': True}, 'evidence': [{'atomic_rule_id': 'AR-2', 'page': 1, 'quote': 'q2'}]},
        ]
        maker_records = [
            {'run_id': 'r1', 'semantic_rule_id': 'SR-1', 'requirement_ids': ['AR-1'], 'feature': 'Feature 1', 'scenarios': [{'scenario_id': 'TC-1', 'case_type': 'positive', 'title': 't', 'intent': 'i', 'priority': 'high', 'given': [], 'when': [], 'then': [], 'assumptions': [], 'evidence': [{'atomic_rule_id': 'AR-1', 'page': 1, 'quote': 'q'}]}]},
            {'run_id': 'r1', 'semantic_rule_id': 'SR-2', 'requirement_ids': ['AR-2'], 'feature': 'Feature 2', 'scenarios': [{'scenario_id': 'TC-2', 'case_type': 'positive', 'title': 't2', 'intent': 'i2', 'priority': 'high', 'given': [], 'when': [], 'then': [], 'assumptions': [], 'evidence': [{'atomic_rule_id': 'AR-2', 'page': 1, 'quote': 'q2'}]}]},
        ]
        checker_reviews = [
            {'case_id': 'TC-1', 'semantic_rule_id': 'SR-1', 'overall_status': 'pass', 'scores': {}, 'coverage_assessment': {'status': 'covered', 'reason': 'ok', 'missing_aspects': []}, 'checker_blocking': False, 'findings': []},
            {'case_id': 'TC-2', 'semantic_rule_id': 'SR-2', 'overall_status': 'pass', 'scores': {}, 'coverage_assessment': {'status': 'covered', 'reason': 'ok', 'missing_aspects': []}, 'checker_blocking': False, 'findings': []},
        ]
        maker_summary = {'run_id': 'r1', 'processed_rule_count': 2, 'scenario_count': 2, 'results_path': str(maker_cases_path)}
        checker_summary = {'run_id': 'r2', 'review_count': 2, 'results_path': str(checker_reviews_path), 'coverage_report_path': str(coverage_report_path)}
        coverage_report = {'total_requirements': 2, 'fully_covered': 2, 'partially_covered': 0, 'uncovered': 0, 'status_by_rule': {'SR-1': {'rule_type': 'permission', 'rule_coverage_status': 'fully_covered', 'rule_pass_status': 'pass', 'required_case_types': ['positive'], 'present_case_types': ['positive'], 'accepted_case_types': ['positive'], 'missing_case_types': []}, 'SR-2': {'rule_type': 'permission', 'rule_coverage_status': 'fully_covered', 'rule_pass_status': 'pass', 'required_case_types': ['positive'], 'present_case_types': ['positive'], 'accepted_case_types': ['positive'], 'missing_case_types': []}}}
        rules_path.write_text(json.dumps(rules, ensure_ascii=False), encoding='utf-8')
        maker_cases_path.write_text('\n'.join(json.dumps(item, ensure_ascii=False) for item in maker_records) + '\n', encoding='utf-8')
        checker_reviews_path.write_text('\n'.join(json.dumps(item, ensure_ascii=False) for item in checker_reviews) + '\n', encoding='utf-8')
        maker_summary_path.write_text(json.dumps(maker_summary, ensure_ascii=False), encoding='utf-8')
        checker_summary_path.write_text(json.dumps(checker_summary, ensure_ascii=False), encoding='utf-8')
        coverage_report_path.write_text(json.dumps(coverage_report, ensure_ascii=False), encoding='utf-8')
        if include_bdd:
            normalized_bdd = {
                'semantic_rule_id': 'SR-1',
                'feature_title': 'Feature 1',
                'scenarios': [
                    {
                        'scenario_id': 'TC-1',
                        'case_type': 'positive',
                        'priority': 'high',
                        'given_steps': [
                            {'step_text': 'custom unmatched setup', 'step_pattern': 'custom unmatched setup'},
                        ],
                        'when_steps': [],
                        'then_steps': [],
                    }
                ],
                'step_definitions': {
                    'given': [
                        {'step_text': 'custom unmatched setup', 'step_pattern': 'custom unmatched setup', 'code': ''},
                    ],
                    'when': [],
                    'then': [],
                },
            }
            normalized_bdd_path.write_text(json.dumps(normalized_bdd, ensure_ascii=False) + '\n', encoding='utf-8')
            bdd_inventory = extract_steps_from_normalized_bdd(normalized_bdd_path)
            library_inventory = extract_steps_from_python_step_defs(Path.cwd() / 'lme_testing' / 'step_library.py')
            report = compute_step_matches(bdd_inventory, library_inventory)
            render_step_visibility_report(bdd_inventory, report, step_registry_path)
        return ReviewSessionManager(
            config=make_config(),
            rules_path=rules_path,
            maker_cases_path=maker_cases_path,
            checker_reviews_path=checker_reviews_path,
            output_root=WORK_TMP / 'sessions',
            repo_root=Path.cwd(),
            rewrite_batch_size=1,
            checker_batch_size=2,
            initial_maker_summary_path=maker_summary_path,
            initial_checker_summary_path=checker_summary_path,
            initial_coverage_report_path=coverage_report_path,
            normalized_bdd_path=normalized_bdd_path if include_bdd else None,
            step_registry_path=step_registry_path if include_bdd else None,
        )


if __name__ == '__main__':
    unittest.main()

