from io import BytesIO

import pandas as pd
import matplotlib.pyplot as plt

from prefect import Flow, task, Parameter, unmapped
from prefect.tasks.secrets import PrefectSecret
from prefect.artifacts import create_markdown
from prefect.storage import GitHub
from prefect.run_configs import DockerRun

from shared_tasks.github import get_stars


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


flow.storage = GitHub("jcrist/prefect-github-example", "flows/github_stars.py")
flow.run_config = DockerRun(image="jcrist/prefect-github-example")
