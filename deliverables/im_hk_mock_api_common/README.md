# Initial Margin Mock API Common Package

Shared deterministic mock API implementation for Initial Margin guide POC deliverables.

This package is intentionally version-neutral. Version-specific packages such as
`deliverables/im_hk_v14_mock_api/` provide thin wrappers for rule catalog labels,
service names, BDD wording, README files, and tests.

Boundaries:

- This is a mock/stub execution bridge, not a production Initial Margin engine.
- It does not replace VaR Platform, HKSCC/HKEX production logic, or Stage 3 real integration.
- Version wrappers must preserve their own review and validation documentation.
