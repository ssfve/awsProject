FROM python:3.8-slim-buster
RUN apt-get update -y

WORKDIR /deposit-app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . /deposit-app

EXPOSE 8080
ENTRYPOINT ["python"]
CMD ["app.py"]