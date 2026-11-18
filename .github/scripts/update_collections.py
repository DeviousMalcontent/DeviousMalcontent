import os
import re
import requests

TOKEN = os.environ["GH_LISTS_TOKEN"]
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

QUERY = """
query {
  viewer {
    lists(first: 32) {
      nodes {
        name
        description
        slug
        items(first: 50) {
          nodes {
            ... on Repository {
              nameWithOwner
              url
              description
            }
          }
        }
      }
    }
  }
}
"""

HOST_API = ".".join(["api", "github", "com"])
API_URL = f"https://{HOST_API}/graphql"

response = requests.post(
    API_URL,
    json={"query": QUERY},
    headers=HEADERS,
)
response.raise_for_status()
data = response.json()

if "errors" in data:
    raise RuntimeError(f"GraphQL API Error: {data['errors']}")

lists = data["data"]["viewer"]["lists"]["nodes"]
username = os.environ["GITHUB_REPOSITORY_OWNER"]
HOST_WEB = ".".join(["github", "com"])

sections = []
for lst in lists:
    items = [item for item in lst["items"]["nodes"] if item]
    if not items:
        continue
    list_url = f"https://{HOST_WEB}/stars/{username}/lists/{lst['slug']}"
    block = [f"### [{lst['name']}]({list_url})"]
    if lst.get("description"):
        block.append(f"*{lst['description']}*\n")
    for repo in items:
        desc = f" - {repo['description']}" if repo.get("description") else ""
        block.append(f"- [{repo['nameWithOwner']}]({repo['url']}){desc}")
    sections.append("\n".join(block))

new_content = "\n\n".join(sections)

with open("README.md", "r", encoding="utf-8") as f:
    readme = f.read()

pattern = r"(<!-- COLLECTIONS:START -->).*?(<!-- COLLECTIONS:END -->)"
updated_readme = re.sub(
    pattern,
    lambda m: f"{m.group(1)}\n{new_content}\n{m.group(2)}",
    readme,
    flags=re.DOTALL,
)

with open("README.md", "w", encoding="utf-8") as f:
    f.write(updated_readme)
