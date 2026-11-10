# foundation-template verification matrix

| Field | Value |
|---|---|
| Document ID | FTEMPLATE-VM |
| Version | 2.3 |
| Status | Baselined |
| Owner | Akilleez-QA |
| Date | 2026-11-10 |
| Baseline commit | fb9993c55e9c708a3cfdd295b237466d4bef7ff1 |
| Applies to | foundation-template main at baseline commit |
| Classification | Self-assessed Class E analog; not safety-critical (see SMP §1) |

> Organized after [NPR 7150.2D](https://nodis3.gsfc.nasa.gov/displayAll.cfm?Internal_ID=N_PR_7150_002D_&page_name=all), [NASA-STD-8739.8B](https://standards.nasa.gov/standard/nasa/nasa-std-87398) and the [NASA Software Engineering Handbook](https://swehb.nasa.gov/display/SWEHBVD/7.18+-+Documentation+Guidance) documentation guidance. This is not a NASA compliance determination or certification. The software classification is a self-assessed analog (Class E, not safety-critical); no NASA authority, independent verification and validation, or hazard analysis is asserted. The document describes the implementation inspected at the baseline commit.

This matrix maps each requirement in the [SRS](../requirements/requirements.md) to the tests or inspection that verify it. `python -B tools/check_trace.py` checks it: every requirement has a row, every referenced test exists, every test traces to a requirement or is listed under "Tests without a requirement", every requirement is allocated in the [SDD](../architecture/architecture.md), and no Markdown link is dead. `tests/test_docs_trace.py` runs that check in the normal test suite, so CI fails on a broken trace. A copy keeps this mechanism and replaces the rows.

Method: T test, I inspection.

| Requirement | Method | Test (file::Class.method) or inspection target | Acceptance observation / limit | Last result |
|---|---|---|---|---|
| REQ-TPL-001 | T | `tests/test_bridge.py::BridgeTests.test_handshake_catalog_and_echo_with_evidence` | `reading 7` is echoed with assessment `observation_echoed` through a real bridge process | [STR-unreleased](reports/STR-unreleased.md) |
| REQ-TPL-002 | T | `tests/test_bridge.py::BridgeTests.test_source_manifest_lists_every_file` | Manifest file map equals the recomputed map exactly | [STR-unreleased](reports/STR-unreleased.md) |
| REQ-TPL-003 | T | `tests/test_bridge.py::BridgeTests.test_handshake_catalog_and_echo_with_evidence` | `boundary` equals `tools.BOUNDARY` | [STR-unreleased](reports/STR-unreleased.md) |
| REQ-TPL-004 | T | `tests/test_bridge.py::BridgeTests.test_handshake_catalog_and_echo_with_evidence`<br>`tests/test_bridge.py::BridgeTests.test_bad_arguments_are_a_tool_error_that_still_carries_evidence` | Success has CHECK Evidence; five bad argument sets each return a tool error with non-empty Evidence | [STR-unreleased](reports/STR-unreleased.md) |
| REQ-TPL-005 | T | `tests/test_bridge.py::BridgeTests.test_handshake_catalog_and_echo_with_evidence` | `input_sha256` equals `tools.input_sha256` of the arguments | [STR-unreleased](reports/STR-unreleased.md) |
| REQ-TPL-006 | I | `foundation_template_bridge/server.py`, `foundation_template_bridge/__main__.py`, `foundation_template/tools.py` | Imports are standard library only (no `socket`, `urllib`, `http`, `subprocess`); no file reads or writes besides stdin, stdout and stderr | [STR-unreleased](reports/STR-unreleased.md) |
| REQ-TPL-006 | T | `tests/test_bridge.py::BridgeTests.test_wire_profile_fails_closed` | `--root /` is refused with exit 2 | [STR-unreleased](reports/STR-unreleased.md) |
| REQ-TPL-007 | T | `tests/test_input_limits.py::InputLimitTests.test_req_tpl_007_frame_bytes`<br>`tests/test_input_limits.py::InputLimitTests.test_req_tpl_007_stream_frame_bytes`<br>`tests/test_input_limits.py::InputLimitTests.test_req_tpl_007_depth`<br>`tests/test_input_limits.py::InputLimitTests.test_req_tpl_007_nodes`<br>`tests/test_input_limits.py::InputLimitTests.test_req_tpl_007_string_characters`<br>`tests/test_input_limits.py::InputLimitTests.test_req_tpl_007_integer_digits`<br>`tests/test_bridge.py::BridgeTests.test_wire_profile_fails_closed` | Each limit accepted at its value and refused one past it with `-32002` | [STR-unreleased](reports/STR-unreleased.md) |
| REQ-TPL-008 | T | `tests/test_bridge.py::BridgeTests.test_handshake_catalog_and_echo_with_evidence`<br>`tests/test_bridge.py::BridgeTests.test_wire_profile_fails_closed`<br>`tests/test_input_limits.py::InputLimitTests.test_req_tpl_007_stream_frame_bytes` | `initialize` result fields; `-32000` before initialize; `-32602` for `read_file`; `ping` returns `{}` | [STR-unreleased](reports/STR-unreleased.md) |
| REQ-TPL-009 | T | `tests/test_bridge.py::BridgeTests.test_handshake_catalog_and_echo_with_evidence` | `tools/list` equals `tool_definitions()` in `TOOL_NAMES` order | [STR-unreleased](reports/STR-unreleased.md) |
| REQ-TPL-010 | T | `tests/test_bridge.py::BridgeTests.test_wire_profile_fails_closed` | Duplicate `id`, `1.5` and `NaN` each give `-32700` | [STR-unreleased](reports/STR-unreleased.md) |
| REQ-TPL-011 | T | `tests/test_bridge.py::BridgeTests.test_handshake_catalog_and_echo_with_evidence`<br>`tests/test_bridge.py::BridgeTests.test_wire_profile_fails_closed`<br>`tests/test_input_limits.py::InputLimitTests.test_req_tpl_007_stream_frame_bytes` | Exit 0 after a complete session; exit 2 for an oversized frame and for `--root /` | [STR-unreleased](reports/STR-unreleased.md) |
| REQ-TPL-012 | T | `tests/test_bridge.py::BridgeTests.test_bad_arguments_are_a_tool_error_that_still_carries_evidence` | `{}`, empty string, integer, extra field and 257 characters are each a tool error | [STR-unreleased](reports/STR-unreleased.md) |
| REQ-TPL-013 | T | `tests/test_gen_reports.py::GenerateReportsTests.test_clean_runs_and_gates_pass`<br>`tests/test_gen_reports.py::GenerateReportsTests.test_main_exits_nonzero_when_gitleaks_finds_a_secret`<br>`tests/test_gen_reports.py::GenerateReportsTests.test_failing_gate_fails_the_report`<br>`tests/test_gen_reports.py::GenerateReportsTests.test_gate_not_run_fails_the_report`<br>`tests/test_gen_reports.py::GenerateReportsTests.test_skipped_test_fails_the_report`<br>`tests/test_gen_reports.py::GenerateReportsTests.test_expected_failure_fails_the_report`<br>`tests/test_gen_reports.py::GenerateReportsTests.test_unparsed_test_outcome_fails_the_report`<br>`tests/test_gen_reports.py::GenerateReportsTests.test_trace_problem_fails_the_report`<br>`tests/test_gen_reports.py::GenerateReportsTests.test_empty_suite_fails_the_report`<br>`tests/test_gen_reports.py::HermeticReportTests.test_verdict_in_empty_repository`<br>`tests/test_gen_reports.py::HermeticReportTests.test_verdict_without_git_directory` | `main()` with stubbed suites and gates: clean runs pass with exit 0; a Gitleaks finding, a stale catalog, a changed manifest, Gitleaks not installed, a skip, an expected failure, an unparsed outcome, a trace problem and an empty suite each give FAILED and exit 1 | [STR-unreleased](reports/STR-unreleased.md) |
| REQ-TPL-014 | T | `tests/test_bridge.py::GapTests.test_gap_tpl_001_handshake_order_and_protocol_version` | Wrong `protocolVersion` gives `-32001` naming the expected protocol and leaves `tools/list` refused with `-32000`; a second `initialize` gives `-32000` "Bridge already initialized"; `tools/list` before `initialize` gives `-32000`; replies keep request order (closes GAP-TPL-001) | [STR-unreleased](reports/STR-unreleased.md) |
| REQ-TPL-015 | T | `tests/test_bridge.py::GapTests.test_gap_tpl_002_oversized_or_unencodable_response_is_withheld` | A response exactly at 1 048 576 bytes is sent unchanged; one byte more gives `-32002` "Result withheld"; NaN, Infinity, a circular reference, a set and an arbitrary object each give `-32603` "Result withheld" with the request `id` (closes GAP-TPL-002) | [STR-unreleased](reports/STR-unreleased.md) |
| REQ-TPL-016 | T | `tests/test_bridge.py::GapTests.test_gap_tpl_003_unexpected_exception_becomes_internal_error` | An exception from the tool or from the inventory gives exactly `-32603` "Internal bridge error; no evidence result is available" with the request `id` and no exception text (closes GAP-TPL-003) | [STR-unreleased](reports/STR-unreleased.md) |
| REQ-TPL-017 | T | `tests/test_bridge.py::GapTests.test_gap_tpl_004_envelope_is_refused_and_notifications_get_no_reply` | 15 malformed envelopes (batch, non-object, extra field, wrong `jsonrpc`, bad `method`, null, boolean, array, object and 129-character `id`) each give `-32600` with a null `id`; a 128-character `id` is accepted; `ping` and `initialize` without `id` get no reply and `initialize` takes no effect (closes GAP-TPL-004) | [STR-unreleased](reports/STR-unreleased.md) |
| REQ-TPL-018 | T | `tests/test_bridge.py::GapTests.test_gap_tpl_005_unterminated_frame_and_broken_pipe_exit_2` | An unterminated last frame gives `-32002` with a null `id` and exit 2, in process and as a child process; a failing sink gives exit 2; a child process whose stdout pipe is closed exits 2 with empty stderr (closes GAP-TPL-005) | [STR-unreleased](reports/STR-unreleased.md) |
| REQ-TPL-019 | T | `tests/test_build_manifest.py::ManifestToolTests.test_gap_tpl_006_inventory_and_manifest_summary`<br>`tests/test_build_manifest.py::ManifestToolTests.test_f7_manifest_version_follows_package_version` | In a copy of the manifest's files, `--inventory` prints the canonical inventory and leaves the manifest unchanged; the normal run prints exactly `files`, `sha256` and `inventory_sha256` matching the written manifest and reproduces the committed one; the manifest `version` equals `__version__` and follows a changed `__version__` (closes GAP-TPL-006 and F-7) | [STR-unreleased](reports/STR-unreleased.md) |
| REQ-TPL-020 | T | `tests/test_gen_reports.py::GenerateReportsTests.test_only_open_gap_rows_count_as_untested`<br>`tests/test_gen_reports.py::GenerateReportsTests.test_report_lists_no_closed_gap_as_untested` | An SRS fixture with one closed and one open gap row, plus gap IDs in prose and rationale, yields only the open row; the report generated from this repository's SRS states 0 untested behaviours and names no gap ID in its summary | [STR-unreleased](reports/STR-unreleased.md) |

## Tests without a requirement

| Test | Classification (supporting / infrastructure / candidate requirement) |
|---|---|
| `tests/test_docs_trace.py::DocumentationTraceTests.test_requirements_trace_to_tests_design_and_live_links` | Infrastructure: documentation trace and link check |
| `tests/test_docs_trace.py::DocumentationTraceTests.test_manifest_copy_passes_its_own_trace_check` | Infrastructure: a copy holding only `SOURCE-MANIFEST.json` and its listed files passes the trace and link check, as a vendoring consumer such as Cstack runs it; links into `.github/`, which the manifest excludes, are skipped only when `.github/` is absent |
| `tests/test_docs_trace.py::DocumentationTraceTests.test_generated_reference_documents_are_current` | Infrastructure: generated tool catalog matches the schemas |
| `tests/test_source_rules.py::SourceRuleTests.test_python_sources_have_no_comments` | Supporting: enforces the no-code-comments design constraint (SRS §10) over every Python file in the package, bridge, tools and tests; added after the Codex review of PR #16 (P1) |
| `tests/test_source_rules.py::SourceRuleTests.test_python_sources_have_no_docstrings` | Supporting: enforces the same constraint for module, class and function docstrings (the F-3 defect class) |
| `tests/test_source_rules.py::SourceRuleTests.test_rule_detects_a_comment_and_a_docstring` | Supporting: shows the two rule checks detect a `noqa` comment and a docstring and ignore a `#` inside a string |

## Change history

| Version | Date | Commit | Change | Reviewed in |
|---|---|---|---|---|
| 1.0 | 2026-10-30 | fbfaadb | Requirement to test-file table | Initial commit |
| 1.1 | 2026-10-30 | 96671fa | REQ-TPL-007 points at `tests/test_input_limits.py` | PR #3 |
| 2.0 | 2026-11-08 | fb9993c | Test-method references; rows for REQ-TPL-008 to REQ-TPL-012; results point to the generated test report | PR adding the NASA-standard documentation set |
| 2.1 | 2026-11-09 | 3814683 | Row for REQ-TPL-013 (test report verdict) | PR fixing the 2026-11-09 backfill-review findings |
| 2.2 | 2026-11-10 | 28ecad1 | Rows for REQ-TPL-014 to REQ-TPL-019, tracing the seven tests that close GAP-TPL-001 to GAP-TPL-006 and F-7 | PR closing the family findings sweep for this repository |
| 2.3 | 2026-11-10 | 4f55f21 | Row for REQ-TPL-020; source-rule tests classified as supporting | Codex review of PR #16 |
