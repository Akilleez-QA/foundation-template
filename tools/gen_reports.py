import argparse
import datetime
import hashlib
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from foundation_template import __version__
from foundation_template_bridge.schemas import tool_definitions

ROOT = Path(__file__).resolve().parents[1]

REPORTS = ROOT / "docs/verification/reports"
RELEASES = ROOT / "docs/releases"
OWNER = "Akilleez-QA"
REPO = "foundation-template"
CODE = "FTEMPLATE"
GAP = "GAP-TPL"
BRIDGE = "foundation_template_bridge"
DASH = "—"
ESCAPED_PIPE = "\\|"
DISCLAIMER = (
    "> Organized after [NPR 7150.2D](https://nodis3.gsfc.nasa.gov/displayAll.cfm?Internal_ID=N_PR_7150_002D_&"
    "page_name=all), [NASA-STD-8739.8B](https://standards.nasa.gov/standard/nasa/nasa-std-87398) and the [NASA "
    "Software Engineering Handbook](https://swehb.nasa.gov/display/SWEHBVD/7.18+-+Documentation+Guidance) "
    "documentation guidance. This is not a NASA compliance determination or certification. The software "
    "classification is a self-assessed analog (Class E, not safety-critical); no NASA authority, independent "
    "verification and validation, or hazard analysis is asserted. The document describes the implementation "
    "inspected at the baseline commit.")
LINE = re.compile(r"^(test_\w+) \(tests\.(test_\w+)\.(\w+)\.test_\w+\) \.\.\. (ok|FAIL|ERROR|skipped.*|expected failure|unexpected success)$")
CONTROL_DOCS = ("docs/plan/software-management-plan.md", "docs/plan/compliance-matrix.md",
                "docs/requirements/requirements.md", "docs/architecture/architecture.md", "docs/icd/icd-cstack.md",
                "docs/data/data-dictionary.md", "docs/verification/test-plan.md",
                "docs/verification/verification-matrix.md", "docs/configuration/configuration-management.md",
                "docs/assurance/assurance-record.md", "docs/guides/SUM-MAP.md")


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def gh(*args):
    if shutil.which("gh") is None:
        return None
    proc = subprocess.run(["gh", *args], cwd=ROOT, capture_output=True, text=True, check=False)
    return proc.stdout if proc.returncode == 0 else None


def run_suite(optimized):
    command = [sys.executable, "-B", *(["-O"] if optimized else []), "-m", "unittest", "discover", "-s", "tests",
               "-t", ".", "-v"]
    proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False,
                          env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    results = {}
    for line in proc.stderr.splitlines():
        match = LINE.match(line)
        if match:
            name, module, cls, outcome = match.groups()
            results[f"tests/{module}.py::{cls}.{name}"] = "skipped" if outcome.startswith("skipped") else outcome
    ran = re.search(r"^Ran (\d+) tests? in ([0-9.]+)s$", proc.stderr, re.M)
    display = f"python -B{' -O' if optimized else ''} -m unittest discover -s tests -t ."
    return {"command": display, "returncode": proc.returncode, "results": results,
            "ran": int(ran.group(1)) if ran else 0, "seconds": ran.group(2) if ran else "unknown",
            "digest": hashlib.sha256(proc.stderr.encode()).hexdigest(), "tail": proc.stderr.strip().splitlines()[-1]}


def run_passed(run):
    return (run["returncode"] == 0 and run["ran"] > 0 and len(run["results"]) == run["ran"]
            and all(outcome == "ok" for outcome in run["results"].values()))


def report_passed(runs, problems, gates):
    return all(run_passed(run) for run in runs) and not problems and all(ok for _, _, ok in gates)


def trace_module():
    spec = importlib.util.spec_from_file_location("check_trace", ROOT / "tools/check_trace.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def requirement_map(trace):
    mapping = {}
    for row in trace.table_rows(trace.VM.read_text(), "| Requirement |"):
        for path, cls, name in trace.TEST_REF.findall(row[2]):
            mapping.setdefault(f"{path}::{cls}.{name}", []).append(row[0])
    return mapping


def source_lines():
    counts = {}
    for name in git("ls-files").splitlines():
        path = ROOT / name
        if not path.is_file():
            continue
        kind = {".py": "Python", ".md": "Markdown", ".json": "JSON", ".yml": "YAML"}.get(path.suffix)
        if kind:
            counts[kind] = counts.get(kind, 0) + len(path.read_bytes().splitlines())
    return counts


def issue_counts():
    raw = gh("issue", "list", "--state", "all", "--limit", "500", "--json", "state,labels")
    if raw is None:
        return None
    issues = json.loads(raw)
    by = {}
    for issue in issues:
        labels = [label["name"] for label in issue["labels"] if re.fullmatch(r"S[1-4]", label["name"])] or ["unlabelled"]
        for label in labels:
            key = (issue["state"].lower(), label)
            by[key] = by.get(key, 0) + 1
    return issues, by


def header(doc_id, title, commit, label, today):
    applies = "main at baseline commit" if label == "unreleased" else label
    return [f"# {REPO} {title}", "", "| Field | Value |", "|---|---|",
            f"| Document ID | {doc_id} |", "| Version | 1.0 |", "| Status | Draft |", f"| Owner | {OWNER} |",
            f"| Date | {today} |", f"| Baseline commit | {commit} |",
            f"| Applies to | {REPO} {applies} |",
            "| Classification | Self-assessed Class E analog; not safety-critical (see SMP §1) |", "", DISCLAIMER,
            "",
            f"Generated by `python -B tools/gen_reports.py --label {label}`. Do not edit by hand; rerun the generator.",
            ""]


def footer(today, commit, change):
    return ["", "## Change history", "", "| Version | Date | Commit | Change | Reviewed in |", "|---|---|---|---|---|",
            f"| 1.0 | {today} | {commit[:7]} | {change} | PR adding the NASA-standard documentation set |"]


def write_str(label, commit, dirty, today, runs, trace, gates):
    problems, summary = trace.check()
    mapping = requirement_map(trace)
    srs = trace.SRS.read_text()
    gaps = sorted(set(re.findall(GAP + r"-\d{3}", srs)))
    tbd = len(re.findall(r"\bTBD\b(?! / question)", srs))
    lines = source_lines()
    issues = issue_counts()
    merged = gh("pr", "list", "--state", "merged", "--limit", "500", "--json", "number")
    normal, optimized = runs
    passed = report_passed(runs, problems, gates)
    conclusion = ("all suites passed with no skips, the trace check found no problems and every gate passed" if passed
                  else "FAILED: see results and problems below")
    dirty_note = " (working tree had uncommitted changes)" if dirty else ""
    now = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M")
    out = header(f"{CODE}-STR-{label.upper()}", f"software test report {label}", commit, label, today)
    out += ["## 1. Summary", "",
            f"- Conclusion: {conclusion}.",
            f"- Remaining deficiencies and limitations: {len(gaps)} untested behaviours are listed as gaps in the "
            f"[requirements](../../requirements/requirements.md#9-untested-behaviour-gaps) "
            f"({', '.join(gaps) or 'none'}). No test exercises a "
            "live host; the Cstack side of the interface is verified in the Cstack repository.",
            "- Test-environment impact: tests read only files in the repository and start the bridge as a child "
            "process. No network or external service is used.", "",
            "## 2. Test log", "", "| Item | Value |", "|---|---|",
            f"| Commit | `{commit}`{dirty_note} |",
            f"| Date (UTC) | {now} |",
            f"| Environment | {platform.system()} {platform.machine()}, CPython {platform.python_version()} |",
            "| Run by | operator, `tools/gen_reports.py` (local run, not CI) |"]
    out += [f"| `{run['command']}` | exit {run['returncode']}, {run['tail']}; {run['ran']} tests in {run['seconds']} s; "
            f"stderr SHA-256 `{run['digest']}` |" for run in runs]
    out += [f"| `python -B tools/check_trace.py` | {len(problems)} problem(s); {summary['requirements']} requirements, "
            f"{summary['traced']} traced; {summary['tests']} tests, {summary['tests_traced']} traced, "
            f"{summary['tests_supporting']} supporting; {summary['markdown_files']} markdown files link-checked |"]
    out += [f"| {name} | {result} |" for name, result, _ in gates]
    out += ["", "## 3. Results", "", "| Test | Requirements | Normal | Optimized (-O) |", "|---|---|---|---|"]
    out += [f"| `{ref}` | {', '.join(mapping.get(ref, [])) or 'supporting'} | "
            f"{normal['results'].get(ref, 'not run')} | {optimized['results'].get(ref, 'not run')} |"
            for ref in sorted(set(normal["results"]) | set(optimized["results"]))]
    out += ["", "## 4. Problems and deviations", ""]
    failures = [(ref, outcome) for run in runs for ref, outcome in run["results"].items() if outcome != "ok"]
    unparsed = [run for run in runs if run["ran"] == 0 or len(run["results"]) != run["ran"]]
    failed_gates = [(name, result) for name, result, ok in gates if not ok]
    if failures or problems or unparsed or failed_gates:
        out += ["| Item | Description |", "|---|---|"]
        out += [f"| `{ref}` | {outcome} |" for ref, outcome in failures]
        out += [f"| `{run['command']}` | {run['ran']} tests ran, {len(run['results'])} outcomes parsed as ok, failed "
                "or skipped |" for run in unparsed]
        out += [f"| {name} | {result} |" for name, result in failed_gates]
        out += [f"| trace | {p.replace('|', ESCAPED_PIPE)} |" for p in problems]
    else:
        out.append("None. No test failed or was skipped, the trace check reported no problems and every gate passed.")
    out += ["", "## 5. Metrics", "", "| Measure | Value | Command |", "|---|---|---|",
            f"| Tests run / passed / failed (normal) | {normal['ran']} / "
            f"{sum(v == 'ok' for v in normal['results'].values())} / "
            f"{sum(v != 'ok' for v in normal['results'].values())} | `{normal['command']}` |",
            f"| Tests run / passed / failed (optimized) | {optimized['ran']} / "
            f"{sum(v == 'ok' for v in optimized['results'].values())} / "
            f"{sum(v != 'ok' for v in optimized['results'].values())} | `{optimized['command']}` |",
            f"| Requirements total / traced to a test or inspection | {summary['requirements']} / {summary['traced']} | "
            "`python -B tools/check_trace.py` |",
            f"| Untested behaviour gaps | {len(gaps)} | count of `{GAP}-` IDs in the SRS |",
            f"| TBD markers in the SRS | {tbd} | count of `TBD` in the SRS |",
            "| Requirement changes since previous tag | no previous tag | `git tag --list` |"]
    if issues is None:
        out.append("| Issues by state and severity | not queried (gh unavailable) | `gh issue list` |")
    else:
        items, by = issues
        text = ", ".join(f"{state} {sev}: {n}" for (state, sev), n in sorted(by.items())) or "none"
        out.append(f"| Issues by state and severity (total {len(items)}) | {text} | `gh issue list --state all` |")
    merged_count = "not queried" if merged is None else len(json.loads(merged))
    out.append(f"| PRs merged (all time) | {merged_count} | `gh pr list --state merged` |")
    out.append(f"| Coverage | not measured: no coverage tool is pinned; see test plan §5 | {DASH} |")
    line_counts = ", ".join(f"{kind} {count}" for kind, count in sorted(lines.items()))
    out.append(f"| Source lines by type (tracked files) | {line_counts} | `git ls-files` + line count |")
    out += ["", "## 6. Rationale for decisions", "",
            "The report is generated from a local run on the operator's machine with the same commands CI runs. "
            "CI results for the same commit are on the pull request's checks page. Coverage is not measured because "
            "the project is standard-library only and no coverage tool is pinned."]
    out += footer(today, commit, "Generated test report")
    (REPORTS / f"STR-{label}.md").write_text("\n".join(out) + "\n")
    return passed


def write_vdd(label, commit, today):
    manifest_raw = (ROOT / "SOURCE-MANIFEST.json").read_bytes()
    manifest = json.loads(manifest_raw)
    inventory = json.dumps(tool_definitions(), ensure_ascii=True, allow_nan=False, sort_keys=True,
                           separators=(",", ":")).encode("ascii")
    tags = git("tag", "--list").split()
    previous = tags[-1] if tags else None
    log = git("log", "--first-parent", "--format=%h %s", *([f"{previous}..{commit}"] if previous else [commit]))
    groups = {}
    for name in manifest["files"]:
        top = name.split("/")[0] if "/" in name else "(root files)"
        groups[top] = groups.get(top, 0) + 1
    tag = label if label != "unreleased" else "none (unreleased main)"
    since = ("No previous tag exists, so this lists every first-parent commit up to the identified commit:"
             if not previous else f"First-parent commits since `{previous}`:")
    out = header(f"{CODE}-VDD-{label.upper()}", f"version description {label}", commit, label, today)
    out += ["## 1. Identification", "", "| Item | Value |", "|---|---|",
            f"| Name | {REPO} |", f"| Version | {__version__} (`foundation_template.__version__`) |",
            f"| Tag | {tag} |",
            f"| Commit | `{commit}` |", f"| Previous tag | {previous or 'none'} |", f"| Date | {today} |", "",
            "## 2. Contents", "",
            "Source tree only. There is no built package and no installer. Files covered by `SOURCE-MANIFEST.json` "
            "by top-level path:", "", "| Path | Files |", "|---|---|"]
    out += [f"| `{top}` | {count} |" for top, count in sorted(groups.items())]
    out += ["", "No third-party code is vendored. The runtime uses the Python standard library only.", "",
            "## 3. Build and install", "", "```sh",
            f"git clone https://github.com/Akilleez-QA/{REPO}", f"cd {REPO}",
            f"git checkout {commit}", "python -B -m unittest discover -s tests -t .",
            "python -B tools/build_manifest.py", "git diff --exit-code SOURCE-MANIFEST.json", "```", "",
            "Requires Python 3.11 or newer (CI uses 3.12). Start the bridge with "
            f"`python -B -m {BRIDGE}` from the repository root.", "",
            "## 4. Integrity", "", "| Item | Value |", "|---|---|",
            f"| `SOURCE-MANIFEST.json` SHA-256 | `{hashlib.sha256(manifest_raw).hexdigest()}` |",
            f"| Manifest file count | {len(manifest['files'])} |",
            f"| Canonical tool inventory SHA-256 | `{hashlib.sha256(inventory).hexdigest()}` |", "",
            "These are the three values a host pins (see the [interface control document](../icd/icd-cstack.md)). "
            "Per-file digests are in `SOURCE-MANIFEST.json`.", "",
            "## 5. Changes since previous tag", "",
            since, "", "```",
            *log.splitlines(), "```", "", "See [CHANGELOG.md](../../CHANGELOG.md) for the summarized changes.", "",
            "## 6. Open problems and workarounds", ""]
    issues = issue_counts()
    if issues is None:
        out.append("Not queried: `gh` was unavailable when this was generated.")
    else:
        open_items = [i for i in issues[0] if i["state"].lower() == "open"]
        out.append(f"Open issues at generation: {len(open_items)} (`gh issue list --state open`).")
    out += ["", "## 7. Documentation baseline", "", "| Document | Baseline commit |", "|---|---|"]
    for name in CONTROL_DOCS:
        match = re.search(r"^\| Baseline commit \| (\S+) \|$", (ROOT / name).read_text(), re.M)
        out.append(f"| [{name}](../../{name}) | {match.group(1) if match else 'not recorded'} |")
    out += ["", "## 8. Verification and scans", "",
            f"Test and trace results for this commit: [STR-{label}](../verification/reports/STR-{label}.md). The "
            "secret scan result is recorded in the same report's test log."]
    out += footer(today, commit, "Generated version description")
    (RELEASES / f"VDD-{label}.md").write_text("\n".join(out) + "\n")


def gitleaks_gate():
    if shutil.which("gitleaks") is None:
        return ("gitleaks", "not run: gitleaks not installed", False)
    proc = subprocess.run(["gitleaks", "git", "--redact", "--no-banner", "--exit-code", "1", "--config",
                           ".gitleaks.toml", "."], cwd=ROOT, capture_output=True, text=True, check=False)
    summary = re.sub(r"\x1b\[[0-9;]*m", "", proc.stdout + proc.stderr).strip().splitlines()
    last = summary[-1] if summary else "no output"
    return ("`gitleaks git --redact --no-banner --exit-code 1 --config .gitleaks.toml .`",
            f"exit {proc.returncode}; {last}", proc.returncode == 0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="unreleased")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9.\-]+", args.label):
        raise SystemExit("label must be lower-case letters, digits, dots or hyphens")
    commit = git("rev-parse", "HEAD")
    dirty = bool(git("status", "--porcelain"))
    today = datetime.date.today().isoformat()
    runs = (run_suite(optimized=False), run_suite(optimized=True))
    manifest = subprocess.run([sys.executable, "-B", "tools/build_manifest.py"], cwd=ROOT, capture_output=True,
                              text=True, check=False)
    diff = subprocess.run(["git", "diff", "--exit-code", "--quiet", "SOURCE-MANIFEST.json"], cwd=ROOT, check=False)
    docs = subprocess.run([sys.executable, "-B", "tools/gen_docs.py", "--check"], cwd=ROOT, capture_output=True,
                          check=False)
    gates = [("`python -B tools/build_manifest.py` then `git diff --exit-code SOURCE-MANIFEST.json`",
              f"exit {manifest.returncode} / {diff.returncode}", manifest.returncode == 0 and diff.returncode == 0),
             ("`python -B tools/gen_docs.py --check`", f"exit {docs.returncode}", docs.returncode == 0),
             gitleaks_gate()]
    REPORTS.mkdir(parents=True, exist_ok=True)
    RELEASES.mkdir(parents=True, exist_ok=True)
    passed = write_str(args.label, commit, dirty, today, runs, trace_module(), gates)
    write_vdd(args.label, commit, today)
    print(json.dumps({"commit": commit, "dirty": dirty, "passed": passed,
                      "normal": runs[0]["returncode"], "optimized": runs[1]["returncode"]}))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
