# MVP Input Document Fixtures

These files are **non-production validation/demo fixtures only**.

They are not real project Test Plan or Regression Pack Index inputs, and they must not be used as evidence that the MVP workflow is ready for a production release.

Purpose:

- exercise the deterministic S2-F3 optional-input readiness path,
- provide stable sample files for unit tests and local demos,
- keep demo inputs separate from real source materials under `docs/materials/`.

Use with:

```powershell
.venv\Scripts\python.exe main.py mvp-document-readiness `
  --test-plan tests\fixtures\mvp_input_documents\sample_test_plan.md `
  --test-plan-version TP-DEMO-1 `
  --regression-pack-index tests\fixtures\mvp_input_documents\sample_regression_pack_index.md `
  --regression-pack-index-version RP-DEMO-1
```

