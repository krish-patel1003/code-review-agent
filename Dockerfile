FROM python:3.10

WORKDIR /code-review-agent

COPY ./requirements.txt /code-review-agent/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code-review-agent/requirements.txt

COPY ./app /code-review-agent/app

CMD ["fastapi", "run", "app/main.py", "--port", "80"]
