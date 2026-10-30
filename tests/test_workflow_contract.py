import os
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "terraform-cd.yml"


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
    def test_apply_does_not_depend_on_matrix_plan_outputs(self) -> None:
        source = WORKFLOW.read_text(encoding="utf-8")
        plan = job_block(source, "plan")
        apply = job_block(source, "apply")

        self.assertIn("strategy:\n", plan)
        self.assertIn("matrix:\n", plan)
        self.assertNotIn("\n    outputs:\n", plan)
        self.assertNotIn("needs.plan.outputs", apply)
        self.assertIn("if: ${{ !inputs.plan_only }}", apply)

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
                    self.assertIn('-backend-config="use_cli=${{ inputs.use_managed_identity }}"', job)
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


if __name__ == "__main__":
    unittest.main()
