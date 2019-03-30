FROM golang:latest
RUN mkdir /app
ADD . /app/
WORKDIR /app

RUN go get -u cloud.google.com/go/pubsub
RUN go build -o main .

CMD ["/app/main"]
