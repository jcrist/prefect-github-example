import requests
import pandas as pd

from prefect import task


query = """
query fetchGithubStars($owner: String!, $name: String!, $cursor: String) {
    repository(owner: $owner, name: $name) {
        stargazers(first: 100, after: $cursor) {
            edges{
                starredAt
            }
            pageInfo {
                endCursor
                hasNextPage
            }
        }
    }
}
"""


@task
def get_stars(repo, token):
    """Get github stars for a repo"""
    owner, name = repo.split("/")
    headers = {"Authorization": f"bearer {token}"}
    dates = []
    cursor = None
    while True:
        out = requests.post(
            "https://api.github.com/graphql",
            json={
                "query": query,
                "variables": {"owner": owner, "name": name, "cursor": cursor},
            },
            headers=headers,
        )
        resp = out.json()
        dates.extend(
            o["starredAt"] for o in resp["data"]["repository"]["stargazers"]["edges"]
        )
        info = resp["data"]["repository"]["stargazers"]["pageInfo"]
        if not info["hasNextPage"]:
            break
        break  # TODO remove
        cursor = info["endCursor"]

    out = pd.Series(1, index=pd.to_datetime(dates))
    out = out.resample("w").sum().cumsum()
    out.index.name = "date"
    out.name = name
    return out
