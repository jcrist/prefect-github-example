FROM prefecthq/prefect:latest

COPY setup.py setup.py
COPY requirements.txt requirements.txt
COPY shared_tasks shared_tasks
RUN pip install -e .
