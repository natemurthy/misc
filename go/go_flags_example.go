package main

import (
	"os"

	"github.com/k0kubun/pp"
	flags "github.com/samv/go-flags"
)

// Config defines all env vars and flags
type Config struct {
	Foo          string `env:"FOO" long:"foo" short:"f" description:"you totally don't need this"`
	KafkaEnabled bool   `env:"KAFKA" long:"enable-kafka" description:"enable logging messages to kafka"`
}

func main() {
	var config = Config{}
	flagParser := flags.NewParser(&config, flags.HelpFlag|flags.PrintErrors)
	flagParser.NamespaceDelimiter = "-"
	flagParser.Command.Name = "foo"
	flagParser.Usage = "{ --my-server wss://HOST:443/ --my-cert... | --message-file=FILE.yaml } [ OPTIONS ]"
	_, err := flagParser.Parse()
	if err != nil {
		if err, ok := err.(*flags.Error); ok && (err.Type == flags.ErrHelp) {
			return
		}
		os.Exit(2)
	}
	pp.Println(config)
}
