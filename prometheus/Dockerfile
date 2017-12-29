FROM python:3.6-alpine3.6

WORKDIR /opt

ADD requirements.txt requirements.txt
ADD main.py main.py

RUN pip install -r requirements.txt

CMD python main.py
