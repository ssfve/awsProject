FROM python:3.8-slim-buster
RUN apt-get update -y

WORKDIR /mortgage-app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . /mortgage-app

EXPOSE 8081
ENTRYPOINT ["python"]
CMD ["app.py"]