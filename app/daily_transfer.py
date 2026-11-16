"""Standard-library-only, fail-closed payload and Git publication boundary."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess


MAX_BYTES = 256 * 1024 * 1024
MAX_FILES = 512


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(body):
    return hashlib.sha256(body).hexdigest()


def inventory(root, bounded=True):
    root = Path(root)
    require(root.is_dir() and not root.is_symlink(), "not a plain directory")
    result = {}
    total = 0
    for path in sorted(root.rglob("*")):
        mode = path.lstat().st_mode
        require(not stat.S_ISLNK(mode), f"link: {path}")
        if stat.S_ISDIR(mode):
            continue
        require(stat.S_ISREG(mode) and not mode & 0o111, f"unsafe mode: {path}")
        require(not bounded or total + path.stat().st_size <= MAX_BYTES, "payload exceeds byte bound")
        body = path.read_bytes()
        total += len(body)
        require(not bounded or total <= MAX_BYTES, "payload exceeds byte bound")
        result[path.relative_to(root).as_posix()] = {"size": len(body), "sha256": digest(body)}
    require(not bounded or len(result) <= MAX_FILES, "payload exceeds file bound")
    return result

def allowed(path, run):
    p = PurePosixPath(path)
    return (str(p) == path and not p.is_absolute() and all(
        re.fullmatch(r"[A-Za-z0-9_.+\-]+", part) and part not in (".", "..", ".git")
        for part in p.parts) and (path in ("index.html", "data/latest.json") or
                                  path.startswith("data/" + run + "/")))


def validate_bundle(bundle, receipt_hash, identity):
    bundle = Path(bundle)
    require(bundle.is_dir() and not bundle.is_symlink(), "bundle mode")
    require(set(p.name for p in bundle.iterdir()) == {"receipt.json", "payload"}, "extra bundle entries")
    receipt_path = bundle / "receipt.json"
    require(receipt_path.is_file() and not receipt_path.is_symlink() and
            not receipt_path.stat().st_mode & 0o111, "receipt mode")
    require(receipt_path.stat().st_size <= 1024 * 1024, "receipt size")
    body = receipt_path.read_bytes()
    require(digest(body) == receipt_hash, "receipt hash mismatch")
    receipt = json.loads(body)
    require(receipt["identity"] == identity, "invocation identity mismatch")
    require(re.fullmatch(r"runs/[A-Za-z0-9_.+\-]+", receipt["run"]), "run path")
    require(receipt["quality"] in ("success", "partial"), "ineligible quality")
    files = inventory(bundle / "payload")
    require(files == receipt["files"], "payload inventory/hash mismatch")
    require({"index.html", "data/latest.json", "data/" + receipt["run"] + "/manifest.json"} <= files.keys(),
            "missing entry points")
    require(all(allowed(path, receipt["run"]) for path in files), "unexpected payload path")
    return receipt


def git(root, *args, check=True, env=None):
    return subprocess.run(["git", "-C", str(root), *args], check=check, capture_output=True,
                          text=True, timeout=60, env=env)


def remote_head(root, branch, expected, env=None):
    result = git(root, "ls-remote", "--symref", "origin", "HEAD", "refs/heads/" + branch, env=env).stdout
    require("ref: refs/heads/" + branch + "\tHEAD\n" in result, "default branch changed")
    refs = [line.split() for line in result.splitlines() if not line.startswith("ref:")]
    require([expected, "refs/heads/" + branch] in refs, "remote base changed")


def publish(root, bundle, receipt_hash, identity, env=None):
    root = Path(root)
    receipt = validate_bundle(bundle, receipt_hash, identity)
    branch, base = identity["branch"], identity["base_sha"]
    require(re.fullmatch(r"[0-9a-f]{40}", base), "base SHA")
    git(root, "check-ref-format", "refs/heads/" + branch)
    require(git(root, "rev-parse", "HEAD").stdout.strip() == base, "checkout base mismatch")
    require(not git(root, "status", "--porcelain", "--untracked-files=all").stdout, "dirty publisher checkout")
    remote_head(root, branch, base, env)
    run = root / "data" / receipt["run"]
    require(not run.exists(), "acquisition already exists")
    for path in receipt["files"]:
        target = root / path
        require(all(not p.is_symlink() for p in (target, *target.parents)), "destination link")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path(bundle) / "payload" / path, target)
        target.chmod(0o644)
    git(root, "add", "--", *receipt["files"])
    changed = git(root, "diff", "--cached", "--name-only").stdout.splitlines()
    require(set(changed) == set(receipt["files"]), "staged paths mismatch")
    for path, facts in receipt["files"].items():
        entry = git(root, "ls-files", "--stage", "--", path).stdout
        require(entry.startswith("100644 "), "staged mode")
        body = subprocess.run(["git", "-C", str(root), "show", ":" + path], check=True,
                              capture_output=True, timeout=60).stdout
        require(len(body) == facts["size"] and digest(body) == facts["sha256"], "staged bytes mismatch")
    git(root, "-c", "user.name=github-actions[bot]", "-c",
        "user.email=41898282+github-actions[bot]@users.noreply.github.com", "commit", "-m",
        "data: daily verified refresh " + receipt["run"].split("/")[1])
    commit = git(root, "rev-parse", "HEAD").stdout.strip()
    require(git(root, "rev-list", "--parents", "-n", "1", commit).stdout.split() == [commit, base],
            "publication parents must equal receipt base")
    remote_head(root, branch, base, env)
    push_exit = "unknown"
    try:
        push_exit = git(root, "push", "--force-with-lease=refs/heads/" + branch + ":" + base,
                        "origin", commit + ":refs/heads/" + branch, check=False, env=env).returncode
    except subprocess.SubprocessError:
        pass  # Never retry an ambiguous push; read back the exact resulting identity below.
    # A response can be lost after acceptance. Only exact read-back proves persistence.
    try:
        remote_head(root, branch, commit, env)
    except (ValueError, subprocess.SubprocessError) as error:
        raise RuntimeError(f"persistence unknown/rejected for {commit}; push exit {push_exit}") from error
    return commit


def auth_env():
    env = os.environ.copy()
    token = env.pop("GH_TOKEN", None)
    if token:
        encoded = base64.b64encode(("x-access-token:" + token).encode()).decode()
        env.update(GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="http.https://github.com/.extraheader",
                   GIT_CONFIG_VALUE_0="AUTHORIZATION: basic " + encoded)
    return env


def identity_from_env():
    branch = os.environ["DEFAULT_BRANCH"]
    require(os.environ["GITHUB_REF"] == "refs/heads/" + branch, "not default branch")
    require(os.environ["GITHUB_EVENT_NAME"] in ("schedule", "workflow_dispatch"), "unexpected event")
    return {"repository": os.environ["GITHUB_REPOSITORY"], "branch": branch,
            "base_sha": os.environ["GITHUB_SHA"], "run_id": os.environ["GITHUB_RUN_ID"],
            "run_attempt": os.environ["GITHUB_RUN_ATTEMPT"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["publish", "pages", "check"])
    parser.add_argument("--bundle")
    parser.add_argument("--receipt-hash")
    parser.add_argument("--commit")
    parser.add_argument("--site")
    args = parser.parse_args()
    identity = identity_from_env()
    if args.mode == "check":
        remote_head(Path.cwd(), identity["branch"], identity["base_sha"], auth_env())
        return
    receipt = validate_bundle(args.bundle, args.receipt_hash, identity)
    if args.mode == "pages":
        remote_head(Path.cwd(), identity["branch"], args.commit, auth_env())
        Path(args.site).mkdir()
        shutil.copyfile(Path(args.bundle) / "payload/index.html", Path(args.site) / "index.html")
        return
    commit = publish(Path.cwd(), args.bundle, args.receipt_hash, identity, auth_env())
    with open(os.environ["GITHUB_OUTPUT"], "a") as output:
        output.write(f"commit={commit}\nquality={receipt['quality']}\n")
    print(f"Persisted {commit}; quality={receipt['quality']}")


if __name__ == "__main__":
    main()
