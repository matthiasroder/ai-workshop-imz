"""Build a static event page and optionally publish it to a configured GitHub repo."""

import base64
import json
import re
import subprocess
from html import escape


PHOTO_NAME = re.compile(r"(\d{6})-([0-9a-f]{24})\.jpg")


def next_photo_name(photos, key):
    sequence = max((int(PHOTO_NAME.fullmatch(name)[1]) for name in photos), default=0) + 1
    return f"{sequence:06d}-{key}.jpg"


def marker(event):
    return f"<!-- event-photo-kit:{event['slug']} -->"


def gallery_html(event, photos):
    title, date, location, description = (
        escape(event.get(key, "")) for key in ("title", "date", "location", "description")
    )
    details = " · ".join(filter(None, (date, location)))
    items = "\n".join(
        f'<li><a href="photos/{name}"><img src="photos/{name}" alt="Event photo {i}" '
        f'width="1080" height="1920" loading="lazy" decoding="async"></a></li>'
        for i, name in enumerate(photos, 1)
    )
    gallery = f'<ol>{items}</ol>' if items else '<p>Photos will appear here as they’re added.</p>'
    return f'''<!doctype html>
{marker(event)}
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Photo stream</title>
<meta name="description" content="{description}">
<style>
  :root {{ color-scheme: dark; --accent: {event['accent']}; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: #121412; color: #f3f5ee; font: 1rem/1.55 system-ui, sans-serif; }}
  main {{ max-width: 68rem; padding: clamp(1.25rem, 4vw, 3rem); margin: auto; }}
  header {{ padding: clamp(2rem, 8vw, 6rem) 0 2.5rem; border-bottom: 1px solid #3d433b; }}
  .eyebrow {{ color: var(--accent); font-size: .78rem; font-weight: 700; letter-spacing: .16em; text-transform: uppercase; }}
  h1 {{ font: 600 clamp(2.7rem, 8vw, 6.5rem)/.98 Georgia, serif; letter-spacing: -.045em; margin: .55em 0 .25em; overflow-wrap: anywhere; }}
  header p {{ max-width: 42rem; color: #d2d7cb; }}
  section {{ margin-top: 2rem; }}
  ol {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 15rem), 1fr)); gap: clamp(.65rem, 2vw, 1.4rem); padding: 0; list-style: none; }}
  a {{ display: block; }}
  a:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 4px; }}
  img {{ display: block; width: 100%; height: auto; border: 1px solid #3d433b; border-radius: .5rem; }}
</style>
</head>
<body>
<main>
  <header>
    <p class="eyebrow">Event photo stream</p>
    <h1>{title}</h1>
    <p>{details}</p>
    <p>{description}</p>
  </header>
  <section aria-labelledby="photos"><h2 id="photos">Photos</h2>{gallery}</section>
</main>
</body>
</html>
'''


READ_STREAM = '''
query($owner: String!, $repo: String!, $ref: String!, $page: String!, $photos: String!) {
  repository(owner: $owner, name: $repo) {
    ref(qualifiedName: $ref) {
      target {
        oid
        ... on Commit {
          page: file(path: $page) { object { ... on Blob { text } } }
          photos: file(path: $photos) { object { ... on Tree { entries { name } } } }
        }
      }
    }
  }
}
'''

COMMIT = '''
mutation($input: CreateCommitOnBranchInput!) {
  createCommitOnBranch(input: $input) { commit { url } }
}
'''


def github(query, variables):
    try:
        result = subprocess.run(
            ["gh", "api", "graphql", "--input", "-"],
            input=json.dumps({"query": query, "variables": variables}),
            text=True, capture_output=True, timeout=90,
        )
    except FileNotFoundError as error:
        raise RuntimeError("Install GitHub CLI and run gh auth login to publish.") from error
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("GitHub request timed out. Rerun to retry.") from error
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "GitHub request failed.")
    return json.loads(result.stdout)["data"]


def publish(event, website, photo_dir):
    repository = website.get("repository", "")
    if not re.fullmatch(r"[A-Za-z0-9-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Set website.repository to the owner/repository you control.")
    branch = website.get("branch", "main")
    folder = website.get("path", "")
    if not re.fullmatch(r"(?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_-]+", folder):
        raise ValueError("Set website.path to a dedicated folder such as docs/events/my-event.")
    owner, repo = repository.split("/")
    data = github(READ_STREAM, {
        "owner": owner, "repo": repo, "ref": f"refs/heads/{branch}",
        "page": f"{folder}/index.html", "photos": f"{folder}/photos",
    })
    ref = (data.get("repository") or {}).get("ref")
    if not ref:
        raise RuntimeError(f"Branch {branch} is unavailable in {repository}.")
    head = ref["target"]
    previous = (head["page"]["object"].get("text") or "") if head["page"] else ""
    if head["page"] and not previous.startswith(f"<!doctype html>\n{marker(event)}\n"):
        raise RuntimeError(f"{folder}/index.html already exists. Choose a dedicated event folder.")
    entries = (head["photos"]["object"].get("entries") or []) if head["photos"] else []
    photos = sorted(entry["name"] for entry in entries if PHOTO_NAME.fullmatch(entry["name"]))
    published = {PHOTO_NAME.fullmatch(name)[2] for name in photos}
    additions = {}
    for source in sorted(photo_dir.glob("*.jpg")):
        match = PHOTO_NAME.fullmatch(source.name)
        if match and match[2] not in published:
            name = next_photo_name(photos, match[2])
            photos.append(name)
            published.add(match[2])
            additions[f"{folder}/photos/{name}"] = source.read_bytes()
    page = gallery_html(event, photos)
    if page != previous:
        additions[f"{folder}/index.html"] = page.encode()
    if not additions:
        return None
    data = github(COMMIT, {"input": {
        "branch": {"repositoryNameWithOwner": repository, "branchName": branch},
        "expectedHeadOid": head["oid"],
        "message": {"headline": f"Update event photo stream: {event['slug']}"},
        "fileChanges": {"additions": [
            {"path": path, "contents": base64.b64encode(content).decode("ascii")}
            for path, content in additions.items()
        ]},
    }})
    return data["createCommitOnBranch"]["commit"]["url"]
