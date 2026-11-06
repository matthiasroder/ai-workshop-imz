"""Append finished IMZ Story JPGs to The Mindshift's GitHub Pages gallery."""

import base64
import hashlib
import json
import re
import subprocess


REPOSITORY = "matthiasroder/themindshift-website"
BRANCH = "main"
PHOTO_DIR = "public/images/events/imz-ai-agents"
EVENT_PAGE = "src/pages/events/imz-ai-agents.astro"
PHOTO_NAME = re.compile(r"(\d{6})-([a-f0-9]{24})\.jpg")

READ_STREAM = """
query($owner: String!, $repo: String!, $ref: String!, $page: String!, $photos: String!) {
  repository(owner: $owner, name: $repo) {
    ref(qualifiedName: $ref) {
      target {
        oid
        ... on Commit {
          page: file(path: $page) { name }
          photos: file(path: $photos) { object { ... on Tree { entries { name } } } }
        }
      }
    }
  }
}
"""
APPEND_PHOTOS = """
mutation($input: CreateCommitOnBranchInput!) {
  createCommitOnBranch(input: $input) { commit { oid url } }
}
"""


def github_graphql(query, variables):
    try:
        result = subprocess.run(
            ["gh", "api", "graphql", "--input", "-"],
            input=json.dumps({"query": query, "variables": variables}),
            capture_output=True,
            text=True,
            timeout=90,
        )
    except FileNotFoundError as error:
        raise RuntimeError("Install GitHub CLI and run gh auth login to sync the website.") from error
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("The GitHub request timed out. Rerun to check for unpublished photos.") from error
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "GitHub API request failed.")
    return json.loads(result.stdout)["data"]


def publish_photos(stories):
    """Publish only new photos, preserving the order of the existing stream."""
    if not stories:
        return
    owner, repo = REPOSITORY.split("/")
    result = github_graphql(READ_STREAM, {
        "owner": owner, "repo": repo, "ref": f"refs/heads/{BRANCH}",
        "page": EVENT_PAGE, "photos": PHOTO_DIR,
    })
    head = result["repository"]["ref"]["target"]
    if not head["page"]:
        raise RuntimeError("The event page is missing from the production branch.")

    entries = head["photos"]["object"]["entries"] if head["photos"] else []
    published = set()
    sequence = 0
    for entry in entries:
        match = PHOTO_NAME.fullmatch(entry["name"])
        if match:
            sequence = max(sequence, int(match[1]))
            published.add(match[2])

    additions = []
    for file_id, story in stories:
        key = hashlib.sha256(file_id.encode()).hexdigest()[:24]
        if key in published:
            continue
        sequence += 1
        published.add(key)
        additions.append({
            "path": f"{PHOTO_DIR}/{sequence:06d}-{key}.jpg",
            "contents": base64.b64encode(story.read_bytes()).decode("ascii"),
        })
    if not additions:
        print("Website photo stream is up to date.", flush=True)
        return

    result = github_graphql(APPEND_PHOTOS, {"input": {
        "branch": {"repositoryNameWithOwner": REPOSITORY, "branchName": BRANCH},
        "expectedHeadOid": head["oid"],
        "message": {"headline": f"Append {len(additions)} IMZ workshop photos"},
        "fileChanges": {"additions": additions},
    }})
    commit = result["createCommitOnBranch"]["commit"]
    print(f"Website deploy queued: {commit['url']}", flush=True)
