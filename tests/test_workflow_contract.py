import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "terraform-cd.yml"
VALIDATOR = REPO_ROOT / ".github" / "scripts" / "reviewed_plan.py"


def job_block(source: str, job_name: str) -> str:
    marker = f"  {job_name}:\n"
    start = source.index(marker)
    remainder = source[start + len(marker) :]
    next_job = next(
        (
            index
            for index, line in enumerate(remainder.splitlines(keepends=True))
            if line.startswith("  ") and not line.startswith("    ") and line.rstrip().endswith(":")
        ),
        None,
    )
    if next_job is None:
        return source[start:]
    prefix = "".join(remainder.splitlines(keepends=True)[:next_job])
    return marker + prefix


class TerraformCdWorkflowContractTests(unittest.TestCase):
    def test_reviewed_plan_uses_explicit_cross_run_reference(self) -> None:
        source = WORKFLOW.read_text(encoding="utf-8")
        apply = job_block(source, "apply")

        for input_name in (
            "retain_plan", "reviewed_plan_run_id", "reviewed_plan_artifact_id",
            "reviewed_plan_sha256",
        ):
            self.assertIn(f"      {input_name}:\n", source)
        self.assertIn("run-id: ${{ inputs.reviewed_plan_run_id }}", apply)
        self.assertIn("artifact-ids: ${{ inputs.reviewed_plan_artifact_id }}", apply)
        self.assertIn("REVIEWED_PLAN_SHA256", apply)
        self.assertNotIn("terraform plan", apply)
        self.assertLess(apply.index("Reject untrusted reviewed-plan artifact"), apply.index("Download exact reviewed plan"))
        self.assertIn("-lockfile=readonly", apply)
        self.assertNotIn("LOCKFILE_ARG", job_block(source, "plan"))
        self.assertIn("github-token: ${{ secrets.reviewed_plan_token }}", apply)
        self.assertNotIn("\n    permissions:\n", apply)
        self.assertIn("inputs.reviewed_plan_run_id == '' || inputs.plan_only", job_block(source, "plan"))

    def test_apply_does_not_depend_on_matrix_plan_outputs(self) -> None:
        source = WORKFLOW.read_text(encoding="utf-8")
        plan = job_block(source, "plan")
        apply = job_block(source, "apply")

        self.assertIn("strategy:\n", plan)
        self.assertIn("matrix:\n", plan)
        self.assertNotIn("\n    outputs:\n", plan)
        self.assertNotIn("needs.plan.outputs", apply)
        self.assertIn("!inputs.plan_only", apply)
        self.assertIn("needs.plan.result == 'success'", apply)

    def test_plan_selection_preserves_legacy_and_blocks_unreviewed_apply(self) -> None:
        source = WORKFLOW.read_text(encoding="utf-8")
        step = job_block(source, "plan").split("      - name: Validate plan selection\n", 1)[1]
        script = textwrap.dedent(step.split("        run: |\n", 1)[1].split("\n      - ", 1)[0])
        candidate = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe"
        bash = str(candidate) if candidate.is_file() else shutil.which("bash")
        self.assertIsNotNone(bash)
        baseline = {
            "REQUIRE_REVIEWED_PLAN": "false", "RETAIN_PLAN": "false", "PLAN_ONLY": "true",
            "RUN_OPA": "true", "DESTROY_MODE": "false", "GITHUB_REF": "refs/heads/main",
            "REVIEWED_PLAN_RUN_ID": "", "REVIEWED_PLAN_ARTIFACT_ID": "", "REVIEWED_PLAN_SHA256": "",
        }
        for overrides, succeeds in (
            ({}, True), ({"PLAN_ONLY": "false"}, True),
            ({"REQUIRE_REVIEWED_PLAN": "true"}, True),
            ({"REQUIRE_REVIEWED_PLAN": "true", "PLAN_ONLY": "false"}, False),
            ({"REVIEWED_PLAN_ARTIFACT_ID": "456"}, False),
            ({"REVIEWED_PLAN_RUN_ID": "123"}, False),
            ({"REVIEWED_PLAN_SHA256": "a" * 64}, False),
            ({"RETAIN_PLAN": "true"}, True),
            ({"RETAIN_PLAN": "true", "PLAN_ONLY": "false"}, False),
            ({"RETAIN_PLAN": "true", "GITHUB_REF": "refs/heads/feature"}, False),
            ({"RETAIN_PLAN": "true", "RUN_OPA": "false"}, False),
            ({"RETAIN_PLAN": "true", "DESTROY_MODE": "true"}, False),
        ):
            with self.subTest(overrides=overrides):
                result = subprocess.run(
                    [bash, "-c", script], env=os.environ | baseline | overrides,
                    capture_output=True, text=True, timeout=15,
                )
                self.assertEqual(result.returncode == 0, succeeds, result.stdout + result.stderr)

    def test_direct_identity_is_opt_in_for_every_deployment_job(self) -> None:
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('      use_managed_identity:\n', source)
        input_block = source.split('      use_managed_identity:\n', 1)[1].split('      runs_on:', 1)[0]
        self.assertIn('type: boolean', input_block)
        self.assertIn('default: false', input_block)
        for job_name in ("plan", "apply", "stamp-last-applied"):
            with self.subTest(job=job_name):
                job = job_block(source, job_name)
                self.assertIn('if: ${{ inputs.use_managed_identity }}', job)
                self.assertIn('AZURE_CORE_USE_MSAL_MANAGED_IDENTITY: "true"', job)
                if job_name != "stamp-last-applied":
                    self.assertIn('ARM_USE_OIDC: ${{ !inputs.use_managed_identity }}', job)
                    self.assertIn('ARM_USE_CLI: ${{ inputs.use_managed_identity }}', job)
                    self.assertIn('-backend-config="use_oidc=${{ !inputs.use_managed_identity }}"', job)
                    self.assertNotIn('-backend-config="use_cli=', job)
                else:
                    self.assertIn('if: ${{ !inputs.use_managed_identity }}', job)

    def test_direct_login_requires_matching_subscription_and_tenant(self) -> None:
        source = WORKFLOW.read_text(encoding="utf-8")
        candidates = [Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe"]
        bash = next((str(path) for path in candidates if path.is_file()), shutil.which("bash"))
        self.assertIsNotNone(bash, "Bash is required to exercise the actual workflow login script")
        for job_name in ("plan", "apply", "stamp-last-applied"):
            job = job_block(source, job_name)
            step = job.split('      - name: Direct managed identity login\n', 1)[1]
            script = textwrap.dedent(step.split('        run: |\n', 1)[1].split('\n      - ', 1)[0])
            for login_status, subscription, tenant, succeeds in (
                (0, "expected-subscription", "expected-tenant", True),
                (7, "expected-subscription", "expected-tenant", False),
                (0, "wrong-subscription", "expected-tenant", False),
                (0, "expected-subscription", "wrong-tenant", False),
            ):
                with self.subTest(job=job_name, login=login_status, subscription=subscription, tenant=tenant):
                    with tempfile.TemporaryDirectory(prefix="terraform-direct-login-") as directory:
                        target = Path(directory)
                        executable = target / "az"
                        executable.write_text(
                            '#!/usr/bin/env bash\n'
                            'printf "%s\\n" "$*" >> "$AUTH_CALL_LOG"\n'
                            'if [[ "$1" == login ]]; then exit "$LOGIN_STATUS"; fi\n'
                            'if [[ "$*" == *"--query id"* ]]; then printf "%s\\n" "$ACTUAL_SUBSCRIPTION"; fi\n'
                            'if [[ "$*" == *"--query tenantId"* ]]; then printf "%s\\n" "$ACTUAL_TENANT"; fi\n',
                            encoding="utf-8", newline="\n",
                        )
                        executable.chmod(0o755)
                        calls = target / "calls.txt"
                        environment = os.environ | {
                            "PATH": str(target) + os.pathsep + os.environ["PATH"],
                            "ARM_CLIENT_ID": "expected-identity",
                            "ARM_SUBSCRIPTION_ID": "expected-subscription",
                            "ARM_TENANT_ID": "expected-tenant",
                            "AUTH_CALL_LOG": calls.as_posix(),
                            "RUNNER_TEMP": target.as_posix(),
                            "GITHUB_ENV": (target / "github.env").as_posix(),
                            "ACTUAL_SUBSCRIPTION": subscription,
                            "ACTUAL_TENANT": tenant,
                            "LOGIN_STATUS": str(login_status),
                        }
                        result = subprocess.run(
                            [bash, "-c", script], env=environment,
                            capture_output=True, text=True, timeout=30,
                        )
                        self.assertEqual(result.returncode == 0, succeeds, result.stdout + result.stderr)
                        actual_calls = calls.read_text(encoding="utf-8").splitlines()
                        self.assertEqual(actual_calls[0], "login --identity --client-id expected-identity --output none")
                        if login_status:
                            self.assertEqual(len(actual_calls), 1)


class ReviewedPlanValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        spec = importlib.util.spec_from_file_location("reviewed_plan", VALIDATOR)
        self.assertIsNotNone(spec)
        self.validator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.validator)
        self.directory = tempfile.TemporaryDirectory(prefix="reviewed-plan-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source = "a" * 40
        self.plan = self.root / "corpus-eus-prd.tfplan"
        self.plan.write_bytes(b"exact reviewed binary")
        Path(str(self.plan) + ".json").write_text('{"resource_changes": []}', encoding="utf-8")
        (self.root / ".terraform.lock.hcl").write_text("exact provider selection", encoding="utf-8")
        self.environment = {
            "GITHUB_REPOSITORY": "owner/stack", "GITHUB_SHA": self.source,
            "GITHUB_REF": "refs/heads/main", "GITHUB_EVENT_NAME": "workflow_dispatch",
            "GITHUB_WORKFLOW_REF": "owner/stack/.github/workflows/terraform-cd.yml@refs/heads/main",
            "GITHUB_RUN_ID": "123", "GITHUB_RUN_ATTEMPT": "1",
            "PLAN_CONFIG": "corpus-eus-prd", "PLAN_CONFIGS": '["corpus-eus-prd"]',
            "PLAN_ENVIRONMENT": "dev", "WORKING_DIR": str(self.root), "TFVARS_DIR": "configs",
            "TERRAFORM_VERSION": "1.9.5", "ARM_TENANT_ID": "tenant",
            "ARM_SUBSCRIPTION_ID": "subscription", "ARM_CLIENT_ID": "identity",
            "STATE_RESOURCE_GROUP": "state-rg", "STATE_STORAGE_ACCOUNT": "state-account",
            "STATE_CONTAINER": "tfstate", "STATE_KEY_PREFIX": "stack",
            "DESTROY_MODE": "false", "ALLOW_RECREATE": "false", "ALLOW_VERSION_ROLLBACK": "false",
            "PLAN_ONLY": "false", "RETAIN_PLAN": "false", "RUN_OPA": "true",
            "REVIEWED_PLAN_RUN_ID": "123", "REVIEWED_PLAN_ARTIFACT_ID": "456",
            "REVIEWED_PLAN_SHA256": hashlib.sha256(self.plan.read_bytes()).hexdigest(),
            "RUN_METADATA_PATH": str(self.root / "run.json"),
            "ARTIFACT_METADATA_PATH": str(self.root / "artifact.json"),
        }
        self.run = {
            "id": 123, "run_attempt": 1, "status": "completed", "conclusion": "success",
            "event": "workflow_dispatch", "head_branch": "main", "head_sha": self.source,
            "path": ".github/workflows/terraform-cd.yml", "repository": {"full_name": "owner/stack", "id": 77},
        }
        self.artifact = {
            "id": 456, "name": "tfplan-corpus-eus-prd", "expired": False,
            "workflow_run": {"id": 123, "head_sha": self.source, "head_branch": "main", "repository_id": 77, "head_repository_id": 77},
        }
        self.write_metadata()
        self.environment_patch = patch.dict(os.environ, self.environment)
        self.environment_patch.start()
        self.addCleanup(self.environment_patch.stop)
        self.validator.record()

    def write_metadata(self) -> None:
        (self.root / "run.json").write_text(json.dumps(self.run), encoding="utf-8")
        (self.root / "artifact.json").write_text(json.dumps(self.artifact), encoding="utf-8")

    def test_exact_reviewed_plan_and_provider_lock_are_accepted(self) -> None:
        self.validator.metadata()
        self.validator.validate()
        destination = self.root / ".terraform.lock.hcl"
        destination.unlink()
        self.validator.validate()
        self.assertEqual(destination.read_text(encoding="utf-8"), "exact provider selection")

    def test_source_and_artifact_mismatches_are_rejected(self) -> None:
        cases = (
            ("run", "id", 999), ("run", "status", "in_progress"),
            ("run", "conclusion", "failure"), ("run", "head_sha", "b" * 40),
            ("run", "head_branch", "feature"), ("run", "path", ".github/workflows/other.yml"),
            ("run", "event", "pull_request"), ("run", "run_attempt", None),
            ("run", "repository", {"full_name": "other/stack", "id": 77}),
            ("artifact", "id", 999), ("artifact", "expired", True),
            ("artifact", "expired", None), ("artifact", "name", "other"),
            ("artifact", "workflow_run", {"id": 999}),
        )
        for target, key, value in cases:
            with self.subTest(target=target, key=key, value=value):
                record = self.run if target == "run" else self.artifact
                original = record[key]
                record[key] = value
                self.write_metadata()
                with self.assertRaises((ValueError, KeyError)):
                    self.validator.metadata()
                record[key] = original
                self.write_metadata()

    def test_binary_json_lock_and_attempt_changes_are_rejected(self) -> None:
        for path in (self.plan, Path(str(self.plan) + ".json"), Path(str(self.plan) + ".lock.hcl")):
            with self.subTest(path=path.name):
                original = path.read_bytes()
                path.write_bytes(b"changed")
                with self.assertRaises(ValueError):
                    self.validator.validate()
                path.write_bytes(original)
        self.run["run_attempt"] = 2
        self.write_metadata()
        with self.assertRaises(ValueError):
            self.validator.validate()

    def test_backend_identity_environment_and_version_changes_are_rejected(self) -> None:
        for variable in (
            "STATE_KEY_PREFIX", "STATE_RESOURCE_GROUP", "STATE_STORAGE_ACCOUNT", "STATE_CONTAINER",
            "ARM_TENANT_ID", "ARM_SUBSCRIPTION_ID", "ARM_CLIENT_ID", "PLAN_ENVIRONMENT", "TERRAFORM_VERSION",
        ):
            with self.subTest(variable=variable), patch.dict(os.environ, {variable: "changed"}):
                with self.assertRaises(ValueError):
                    self.validator.validate()

    def test_invalid_or_incomplete_request_is_rejected(self) -> None:
        for variable, value in (
            ("REVIEWED_PLAN_RUN_ID", ""), ("REVIEWED_PLAN_ARTIFACT_ID", ""),
            ("REVIEWED_PLAN_SHA256", ""), ("REVIEWED_PLAN_RUN_ID", "123/other"),
            ("GITHUB_EVENT_NAME", "push"), ("GITHUB_REF", "refs/heads/feature"),
            ("RUN_OPA", "false"), ("PLAN_ONLY", "true"), ("RETAIN_PLAN", "true"),
            ("PLAN_CONFIGS", '["corpus-eus-prd", "other"]'),
        ):
            with self.subTest(variable=variable), patch.dict(os.environ, {variable: value}):
                with self.assertRaises(ValueError):
                    self.validator.validate()

    def test_conflicting_provider_lock_is_not_overwritten(self) -> None:
        destination = self.root / ".terraform.lock.hcl"
        destination.write_text("unrelated provider selection", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.validator.validate()
        self.assertEqual(destination.read_text(encoding="utf-8"), "unrelated provider selection")

    def test_safety_flag_changes_are_rejected(self) -> None:
        for variable in ("DESTROY_MODE", "ALLOW_RECREATE", "ALLOW_VERSION_ROLLBACK"):
            with self.subTest(variable=variable), patch.dict(os.environ, {variable: "true"}):
                with self.assertRaises(ValueError):
                    self.validator.validate()

    def test_changed_validator_requires_a_new_reviewed_plan(self) -> None:
        changed = self.root / "changed_validator.py"
        changed.write_bytes(VALIDATOR.read_bytes() + b"\n")
        with patch.object(self.validator, "__file__", str(changed)):
            with self.assertRaises(ValueError):
                self.validator.validate()

    def test_record_rejects_unchecked_or_destroy_plan_before_retention(self) -> None:
        lock = Path(str(self.plan) + ".lock.hcl")
        receipt = Path(str(self.plan) + ".receipt.json")
        lock.unlink()
        receipt.unlink()
        for overrides in ({"RUN_OPA": "false"}, {"DESTROY_MODE": "true"}):
            with self.subTest(overrides=overrides), patch.dict(os.environ, overrides):
                with self.assertRaises(ValueError):
                    self.validator.record()
                self.assertFalse(lock.exists())
                self.assertFalse(receipt.exists())

    def test_missing_or_malformed_metadata_fails_closed(self) -> None:
        path = self.root / "run.json"
        for content in ("", "[]", "null", "{", "{}"):
            with self.subTest(content=content):
                path.write_text(content, encoding="utf-8")
                with self.assertRaises((ValueError, KeyError)):
                    self.validator.metadata()
        path.unlink()
        with self.assertRaises(OSError):
            self.validator.metadata()


if __name__ == "__main__":
    unittest.main()
