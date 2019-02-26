package main

import (
	"crypto/tls"
	"crypto/x509"
	"flag"
	"io/ioutil"
	"log"
	"strings"

	"github.com/k0kubun/pp"
	schemaregistry "github.com/teslamotors/schema-registry"
)

// a tool to determine which kafka topics have messages encoded in avro based on
// subject names listed in the schema registry server

var (
	baseURL = flag.String(
		"url",
		"avro-schemas.kafka-prod",
		"base URL of schema registry server",
	)

	caFile   = flag.String("cacert", "ca.pem", "path to cacert")
	certFile = flag.String("cert", "cert.pem", "path to cert")
	keyFile  = flag.String("key", "key.pem", "path to key")
)

func NewRegistryClient() (*schemaregistry.Client, error) {
	clientCert, err := tls.LoadX509KeyPair(*certFile, *keyFile)
	if err != nil {
		log.Fatalf("failed to create x509 key pair: %v", err)
	}

	certPool := x509.NewCertPool()
	caCert, err := ioutil.ReadFile(*caFile)
	if err != nil {
		log.Fatal("failed to read CA cert")
	}

	ok := certPool.AppendCertsFromPEM(caCert)
	if !ok {
		log.Fatal("failed to create cert pool")
	}

	serverName := strings.TrimSuffix(strings.TrimPrefix(*baseURL, "https://"), "/")

	tlsConfig := &tls.Config{
		ServerName:   serverName,
		Certificates: []tls.Certificate{clientCert},
		RootCAs:      certPool,
	}

	return schemaregistry.NewTlsClient(*baseURL, tlsConfig)
}

func GetAvroTopics(subjects []string) []string {
	m := make(map[string]struct{})
	for _, s := range subjects {
		m[strings.TrimSuffix(strings.TrimSuffix(s, "-key"), "-value")] = struct{}{}
	}
	topics := []string{}
	for t := range m {
		topics = append(topics, t)
	}
	return topics
}

func main() {
	flag.Parse()

	client, err := NewRegistryClient()
	if err != nil {
		panic(err)
	}

	subjects, err := client.Subjects()
	if err != nil {
		panic(err)
	}

	pp.Println(GetAvroTopics(subjects))
}
