FROM python:3.6-alpine3.6

ADD . /solver-service
WORKDIR /solver-service

RUN apk add --update --no-cache g++ gfortran linux-headers make musl-dev python3-dev
RUN pip install grpcio numpy
RUN apk del g++ gfortran linux-headers make musl-dev python3-dev

CMD ["python", "server.py"]
