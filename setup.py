from setuptools import setup

with open("requirements.txt") as fil:
    install_requires = fil.read().strip().split("\n")

setup(
    name="shared_tasks",
    version="0.0.1",
    packages=["shared_tasks"],
    description="Shared tasks for my prefect flows",
    install_requires=install_requires,
)
