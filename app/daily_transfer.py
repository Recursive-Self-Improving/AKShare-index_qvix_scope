"""Standard-library-only, fail-closed payload and Git publication boundary."""
import argparse
import base64
import hashlib
from datetime import datetime, timedelta
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
        info = path.lstat()
        require(not stat.S_ISLNK(info.st_mode), f"link: {path}")
        if stat.S_ISDIR(info.st_mode):
            continue
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and not info.st_mode & 0o111,
                f"unsafe mode: {path}")
        require(not bounded or total + info.st_size <= MAX_BYTES, "payload exceeds byte bound")
        body = path.read_bytes()
        total += len(body)
        require(not bounded or total <= MAX_BYTES, "payload exceeds byte bound")
        result[path.relative_to(root).as_posix()] = {"size": len(body), "sha256": digest(body)}
    require(not bounded or len(result) <= MAX_FILES, "payload exceeds file bound")
    return result

def payload_inventory(root):
    files = inventory(root)
    manifest = "data/current/manifest.json"
    require({"index.html", manifest} <= files.keys(), "missing entry points")
    snapshot = json.loads((root / manifest).read_bytes())
    feeds = snapshot["feeds"]
    require(isinstance(feeds, dict), "invalid feed registry")
    current = PurePosixPath("data/current")
    group = current / "qvix-group"
    directories = {current, current.parent}
    transport = {"transport.json"}
    shared = transport | {"config.json", "group.json", "termination.json"}
    index = transport | {"result.json", "observations.csv", "terminated.json"}
    qvix = {"result.json", "observations.csv", "invocation.json", "wrapper.csv", "quality.json"}
    expected = {group: shared}
    for feed in feeds:
        require(re.fullmatch(r"[A-Za-z0-9_+\-]+", feed), "invalid feed path")
        if feed.startswith("qvix_"):
            expected[group / feed] = qvix
        else:
            expected[current / feed] = index
    for path in files.keys() - {"index.html", manifest}:
        p = PurePosixPath(path)
        names = expected.get(p.parent, ())
        require(p.name in names or "transport.json" in names and re.fullmatch(r"response-[0-9]+\.body", p.name),
                f"unexpected payload path: {path}")
        directories.update(p.parents[:-1])
    require({PurePosixPath(p.relative_to(root).as_posix()) for p in root.rglob("*") if p.is_dir()} ==
            directories, "unexpected payload directory")
    return files, snapshot["attempted_at"]


def validate_bundle(bundle, receipt_hash, identity):
    bundle = Path(bundle)
    require(bundle.is_dir() and not bundle.is_symlink(), "bundle mode")
    require(set(p.name for p in bundle.iterdir()) == {"receipt.json", "payload"}, "extra bundle entries")
    receipt_path = bundle / "receipt.json"
    require(receipt_path.is_file() and not receipt_path.is_symlink() and
            receipt_path.stat().st_nlink == 1 and not receipt_path.stat().st_mode & 0o111, "receipt mode")
    require(receipt_path.stat().st_size <= 1024 * 1024, "receipt size")
    body = receipt_path.read_bytes()
    require(digest(body) == receipt_hash, "receipt hash mismatch")
    receipt = json.loads(body)
    require(receipt["identity"] == identity, "invocation identity mismatch")
    require(receipt["quality"] in ("success", "partial"), "ineligible quality")
    files, attempted_at = payload_inventory(bundle / "payload")
    require(files == receipt["files"], "payload inventory/hash mismatch")
    require(receipt["attempted_at"] == attempted_at and
            datetime.fromisoformat(attempted_at).utcoffset() == timedelta(0), "acquisition identity")
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
    data, current, html = root / "data", root / "data/current", root / "index.html"
    require(all(not p.is_symlink() for p in (root, *root.parents, data, current, html)), "destination link")
    require(not current.exists() or current.is_dir(), "destination snapshot mode")
    if current.exists():
        shutil.rmtree(current)
    html.unlink(missing_ok=True)
    for path in receipt["files"]:
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path(bundle) / "payload" / path, target)
        target.chmod(0o644)
    git(root, "add", "-Af", "--", "data/current", "index.html")
    changed = git(root, "diff", "--cached", "--name-only", "-z", "--no-renames").stdout.split("\0")[:-1]
    require(changed and all(path == "index.html" or path.startswith("data/current/") for path in changed),
            "staged paths mismatch")
    staged = git(root, "ls-files", "--stage", "-z", "--", "data/current", "index.html").stdout.split("\0")[:-1]
    require(len(staged) == len(receipt["files"]), "staged snapshot inventory mismatch")
    for entry in staged:
        metadata, path = entry.split("\t", 1)
        mode, _, stage = metadata.split()
        require(mode == "100644" and stage == "0" and path in receipt["files"], "staged snapshot path/mode")
        facts = receipt["files"][path]
        body = subprocess.run(["git", "-C", str(root), "show", ":" + path], check=True,
                              capture_output=True, timeout=60).stdout
        require(len(body) == facts["size"] and digest(body) == facts["sha256"], "staged bytes mismatch")
    tree = git(root, "write-tree").stdout.strip()
    git(root, "-c", "user.name=github-actions[bot]", "-c",
        "user.email=41898282+github-actions[bot]@users.noreply.github.com", "commit", "-m",
        "data: daily verified refresh " + receipt["attempted_at"])
    commit = git(root, "rev-parse", "HEAD").stdout.strip()
    require(git(root, "rev-list", "--parents", "-n", "1", commit).stdout.split() == [commit, base],
            "publication parents must equal receipt base")
    require(git(root, "rev-parse", commit + "^{tree}").stdout.strip() == tree, "publication tree changed")
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
        packaged = Path(args.site) / "index.html"
        require(digest(packaged.read_bytes()) == receipt["files"]["index.html"]["sha256"], "Pages HTML hash")
        return
    commit = publish(Path.cwd(), args.bundle, args.receipt_hash, identity, auth_env())
    with open(os.environ["GITHUB_OUTPUT"], "a") as output:
        output.write(f"commit={commit}\nquality={receipt['quality']}\n")
    print(f"Persisted {commit}; quality={receipt['quality']}")


if __name__ == "__main__":
    main()
