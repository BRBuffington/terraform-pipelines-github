from pathlib import Path
import unittest


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


if __name__ == "__main__":
    unittest.main()