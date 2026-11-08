import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

WORKFLOW_PATH = Path(__file__).resolve().parents[1] / "workflows" / "terraform-cd.yml"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def shared_workflow(run, repository):
    expected = repository.split("/", 1)[0] + "/terraform-pipelines-github/.github/workflows/terraform-cd.yml"
    references = run.get("referenced_workflows")
    require(isinstance(references, list), "Reusable workflow metadata is missing")
    matches = [item for item in references if isinstance(item, dict) and str(item.get("path", "")).split("@", 1)[0] == expected]
    require(len(matches) == 1, "Reusable workflow reference is missing or ambiguous")
    require(re.fullmatch(r"[0-9a-f]{40}", matches[0].get("sha", "")), "Invalid reusable workflow revision")
    return {"path": matches[0]["path"], "sha": matches[0]["sha"]}


def context():
    fields = {
        "repository": "GITHUB_REPOSITORY", "source": "GITHUB_SHA",
        "configuration": "PLAN_CONFIG", "environment": "PLAN_ENVIRONMENT",
        "working_dir": "WORKING_DIR", "tfvars_dir": "TFVARS_DIR",
        "terraform_version": "TERRAFORM_VERSION", "tenant": "ARM_TENANT_ID",
        "subscription": "ARM_SUBSCRIPTION_ID", "client_id": "ARM_CLIENT_ID",
        "backend_resource_group": "STATE_RESOURCE_GROUP",
        "backend_storage_account": "STATE_STORAGE_ACCOUNT",
        "backend_container": "STATE_CONTAINER", "backend_prefix": "STATE_KEY_PREFIX",
    }
    result = {name: os.environ[variable] for name, variable in fields.items()}
    require(all(result.values()), "Plan context is incomplete")
    require(re.fullmatch(r"[0-9a-f]{40}", result["source"]), "Invalid source SHA")
    require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", result["configuration"]), "Invalid configuration")
    require(json.loads(os.environ["PLAN_CONFIGS"]) == [result["configuration"]], "Reviewed plans require one configuration")
    require(os.environ["GITHUB_REF"] == "refs/heads/main", "Reviewed plans require main")
    workflow = os.environ["GITHUB_WORKFLOW_REF"].split("@", 1)[0]
    prefix = result["repository"] + "/"
    require(workflow.startswith(prefix), "Workflow owner does not match")
    result["workflow"] = workflow[len(prefix):]
    result["backend_key"] = result["backend_prefix"] + "/" + result["configuration"] + ".tfstate"
    result["validator_sha256"] = digest(Path(__file__))
    result["shared_workflow_sha256"] = digest(WORKFLOW_PATH)
    policy_root = WORKFLOW_PATH.parents[2] / "policy"
    require(policy_root.is_dir() and not policy_root.is_symlink(), "Policy directory is missing or invalid")
    policy_files = sorted(policy_root.rglob("*.rego"))
    require(policy_files and all(path.is_file() and not path.is_symlink() for path in policy_files), "Policy files are missing or invalid")
    result["policy_sha256"] = {path.relative_to(policy_root).as_posix(): digest(path) for path in policy_files}
    current = read_object(os.environ["CURRENT_RUN_METADATA_PATH"])
    require(type(current.get("id")) is int and str(current["id"]) == os.environ["GITHUB_RUN_ID"], "Wrong current run")
    require(type(current.get("run_attempt")) is int and str(current["run_attempt"]) == os.environ["GITHUB_RUN_ATTEMPT"], "Wrong current attempt")
    require(current["repository"]["full_name"] == result["repository"] and current["head_sha"] == result["source"], "Wrong current source")
    require(current["path"] == result["workflow"], "Wrong current workflow")
    result["shared_workflow"] = shared_workflow(current, result["repository"])
    authentication = (os.environ["ARM_USE_OIDC"], os.environ["ARM_USE_CLI"])
    require(authentication in (("true", "false"), ("false", "true")), "Invalid authentication mode")
    result["authentication_mode"] = "oidc" if authentication[0] == "true" else "managed_identity"
    for name in ("DESTROY_MODE", "ALLOW_RECREATE", "ALLOW_VERSION_ROLLBACK"):
        value = os.environ[name]
        require(value in ("true", "false"), "Invalid plan safety input")
        result[name.lower()] = value == "true"
    return result


def paths(configuration, root=None):
    root = root or Path(os.environ["WORKING_DIR"])
    base = root / (configuration + ".tfplan")
    return root, base, Path(str(base) + ".json"), Path(str(base) + ".lock.hcl"), Path(str(base) + ".receipt.json")


def reference():
    require(os.environ["GITHUB_EVENT_NAME"] == "workflow_dispatch", "Reviewed apply requires manual dispatch")
    require(os.environ["GITHUB_REF"] == "refs/heads/main", "Reviewed apply requires main")
    require(os.environ["RUN_OPA"] == "true", "Reviewed apply requires the existing policy gate")
    require(os.environ["PLAN_ONLY"] == "false", "Reviewed reference is apply-only")
    require(os.environ["RETAIN_PLAN"] == "false", "Reviewed apply cannot retain a new plan")
    run_id = os.environ["REVIEWED_PLAN_RUN_ID"]
    artifact_id = os.environ["REVIEWED_PLAN_ARTIFACT_ID"]
    plan_hash = os.environ["REVIEWED_PLAN_SHA256"]
    require(re.fullmatch(r"[1-9][0-9]*", run_id), "Invalid reviewed run ID")
    require(re.fullmatch(r"[1-9][0-9]*", artifact_id), "Invalid reviewed artifact ID")
    require(re.fullmatch(r"[0-9a-f]{64}", plan_hash), "Invalid reviewed plan SHA256")
    return int(run_id), int(artifact_id), plan_hash


def read_object(path):
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    require(isinstance(value, dict), "Expected a JSON object")
    return value


def record():
    snapshot = context()
    require(os.environ["RUN_OPA"] == "true", "Retained review requires the existing policy gate")
    require(not snapshot["destroy_mode"], "Retained review requires a non-destroy policy-checked plan")
    root, plan, rendered, lock, receipt = paths(snapshot["configuration"])
    lock_bytes = (root / ".terraform.lock.hcl").read_bytes()
    with lock.open("xb") as output:
        output.write(lock_bytes)
    result = {
        "schema": 1, "context": snapshot, "run_id": os.environ["GITHUB_RUN_ID"],
        "run_attempt": os.environ["GITHUB_RUN_ATTEMPT"],
        "plan_sha256": digest(plan), "json_sha256": digest(rendered), "lock_sha256": digest(lock),
    }
    with receipt.open("x", encoding="utf-8") as output:
        output.write(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


def metadata():
    run_id, artifact_id, plan_hash = reference()
    snapshot = context()
    run = read_object(os.environ["RUN_METADATA_PATH"])
    artifact = read_object(os.environ["ARTIFACT_METADATA_PATH"])
    require(type(run.get("id")) is int and run["id"] == run_id, "Wrong source run")
    require(run.get("status") == "completed" and run.get("conclusion") == "success", "Source run did not succeed")
    require(run.get("event") in ("push", "workflow_dispatch"), "Untrusted source event")
    require(run.get("head_branch") == "main" and run.get("head_sha") == snapshot["source"], "Source revision changed")
    require(run.get("path") == snapshot["workflow"], "Wrong source workflow")
    repository = run["repository"]
    require(repository["full_name"] == snapshot["repository"], "Wrong source repository")
    require(shared_workflow(run, snapshot["repository"]) == snapshot["shared_workflow"], "Reusable workflow revision changed")
    require(type(artifact.get("id")) is int and artifact["id"] == artifact_id, "Wrong artifact ID")
    require(artifact.get("expired") is False, "Artifact expired or unreadable")
    require(artifact.get("name") == "tfplan-" + snapshot["configuration"], "Wrong artifact name")
    source = artifact["workflow_run"]
    require(source["id"] == run_id and source["head_sha"] == snapshot["source"] and source["head_branch"] == "main", "Artifact source mismatch")
    require(source["repository_id"] == repository["id"] and source["head_repository_id"] == repository["id"], "Artifact belongs to another repository")
    require(type(run.get("run_attempt")) is int and run["run_attempt"] > 0, "Source attempt is missing")
    return run_id, artifact_id, plan_hash, snapshot, run


def validate():
    run_id, artifact_id, plan_hash, snapshot, run = metadata()
    root = Path(os.environ["WORKING_DIR"])
    bundle = Path(os.environ["REVIEWED_PLAN_DIRECTORY"])
    workspace = Path(os.environ["GITHUB_WORKSPACE"]).resolve()
    require(not bundle.is_symlink() and not bundle.resolve().is_relative_to(workspace), "Plan bundle must be outside the checkout")
    _, plan, rendered, lock, receipt = paths(snapshot["configuration"], bundle)
    expected = (plan, rendered, lock, receipt)
    require(set(bundle.iterdir()) == set(expected), "Unexpected plan bundle contents")
    require(all(path.is_file() and not path.is_symlink() for path in expected), "Plan bundle must contain only regular files")
    saved = read_object(receipt)
    require(type(saved.get("schema")) is int and saved["schema"] == 1, "Unsupported plan receipt")
    require(saved.get("context") == snapshot, "Plan context or backend changed")
    require(saved.get("run_id") == str(run_id) and saved.get("run_attempt") == str(run["run_attempt"]), "Plan attempt changed")
    require(saved.get("plan_sha256") == plan_hash and digest(plan) == plan_hash, "Reviewed plan bytes changed")
    require(digest(rendered) == saved["json_sha256"], "Reviewed plan JSON changed")
    require(digest(lock) == saved["lock_sha256"], "Provider lockfile changed")
    destinations = ((root / plan.name, plan, plan_hash), (root / ".terraform.lock.hcl", lock, saved["lock_sha256"]))
    for destination, source, expected_hash in destinations:
        require(not destination.is_symlink(), "Plan destination cannot be a symlink")
        if destination.exists():
            require(digest(destination) == expected_hash, "Source file conflicts with reviewed plan")
    for destination, source, expected_hash in destinations:
        if not destination.exists():
            with destination.open("xb") as output:
                output.write(source.read_bytes())
    print(json.dumps({"verified": True, "run_id": run_id, "artifact_id": artifact_id, "plan_sha256": plan_hash}))
    return snapshot, plan, rendered


def verify_rendered():
    snapshot, plan, reviewed = validate()
    root = Path(os.environ["WORKING_DIR"])
    rendered = Path(os.environ["REVIEWED_PLAN_RENDERED_PATH"])
    with rendered.open("x", encoding="utf-8") as output:
        subprocess.run(
            ["terraform", "show", "-json", str((root / plan.name).resolve())],
            cwd=root, stdout=output, check=True, timeout=90,
        )
    actual = json.dumps(read_object(rendered), sort_keys=True, allow_nan=False)
    approved = json.dumps(read_object(reviewed), sort_keys=True, allow_nan=False)
    require(actual == approved, "Saved binary does not represent reviewed JSON")
    print(json.dumps({"rendered_verified": True, "configuration": snapshot["configuration"]}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("record", "request", "metadata", "validate", "verify-rendered"))
    command = parser.parse_args().command
    try:
        {"record": record, "request": reference, "metadata": metadata, "validate": validate, "verify-rendered": verify_rendered}[command]()
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print("Reviewed plan blocked: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
