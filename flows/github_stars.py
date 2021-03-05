from io import BytesIO

import requests
import pandas as pd
import matplotlib.pyplot as plt

from prefect import Flow, task, Parameter, unmapped
from prefect.tasks.secrets import PrefectSecret
from prefect.artifacts import create_markdown
from prefect.storage import GitHub
from prefect.run_configs import DockerRun


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
        cursor = info["endCursor"]

    out = pd.Series(1, index=pd.to_datetime(dates))
    out = out.resample("w").sum().cumsum()
    out.index.name = "date"
    out.name = name
    return out


@task
def build_df(star_counts):
    """Concatenate star counts into a single dataframe"""
    return pd.concat(star_counts, axis=1).fillna(0)


@task
def make_plot(df):
    """Make a plot of the star counts and post it as an artifact"""
    df.plot.line(title="GitHub Stars")
    fil = BytesIO()
    plt.savefig(fil, format="svg")
    fig_body = fil.getvalue().decode("utf-8")
    create_markdown(fig_body)


with Flow("github_stars") as flow:
    repos = Parameter("repos", default=["prefecthq/prefect", "dagster-io/dagster"])
    token = PrefectSecret("GITHUB_API_TOKEN")

    star_counts = get_stars.map(repos, token=unmapped(token))
    df = build_df(star_counts)
    make_plot(df)


flow.storage = GitHub("prefecthq/prefect", "flows/github_stars.py")
flow.run_config = DockerRun(image="jcrist/prefect-github-example")
