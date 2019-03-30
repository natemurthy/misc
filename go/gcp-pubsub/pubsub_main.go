// Copyright 2017 Google Inc. All rights reserved.
// Use of this source code is governed by the Apache 2.0
// license that can be found in the LICENSE file.

// Sample pubsub_main publishes to a Google Cloud Pub/Sub tpoic and/or subscribes
// from a Google Cloud Pub/Sub subscription.
package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"os"
	"sync"
	"time"

	// Imports the Google Cloud Pub/Sub client package.
	"cloud.google.com/go/pubsub"
)

var (
	numToPublish   = flag.Int("num_msgs_to_publish", 1000000, "The number of messages to publish.")
	numToSubscribe = flag.Int("num_msgs_to_subscribe", 1000000, "The number of messages to subscribe.")

	count    int
	received int
)

func main() {
	flag.Parse()

	ctx := context.Background()

	// Reads your Google Cloud Platform project ID.
	projectID := os.Getenv("GOOGLE_CLOUD_PROJECT_ID")
	if projectID == "" {
		log.Fatalf("GOOGLE_CLOUD_PROJECT_ID environment variable must be set.")
	}

	// Creates a pubsub client.
	client, err := pubsub.NewClient(ctx, projectID)
	if err != nil {
		log.Fatalf("Failed to create pubsub client: %v", err)
	}

	// Reads your Pub/Sub topic name.
	topicName := os.Getenv("GOOGLE_CLOUD_PUBSUB_TOPIC")
	var topic *pubsub.Topic
	if topicName == "" {
		log.Println("GOOGLE_CLOUD_PUBSUB_TOPIC environment variable is not set.")
	} else {
		topic = client.Topic(topicName)
		if ok, err := topic.Exists(ctx); !ok || err != nil {
			log.Fatalf("Failed to read a pubsub topic: ok=%v; err=%v", ok, err)
		}
		log.Printf("Topic %v found.\n", topic)
	}

	// Reads your Pub/Sub subscription name.
	subscriptionName := os.Getenv("GOOGLE_CLOUD_PUBSUB_SUBSCRIPTION")
	var subscription *pubsub.Subscription
	if subscriptionName == "" {
		log.Println("GOOGLE_CLOUD_PUBSUB_SUBSCRIPTION environment variable is not set.")
	} else {
		subscription = client.Subscription(subscriptionName)
		if ok, err := subscription.Exists(ctx); !ok || err != nil {
			log.Fatalf("Failed to read a pubsub subscription: ok=%v; err=%v", ok, err)
		}
		log.Printf("Subscription %v found.\n", subscription)
	}

	go func() {
		for {
			log.Println("total messages written", count)
			time.Sleep(time.Second)
			if count == *numToPublish {
				break
			}
		}
	}()

	if topic != nil {
		// Publish messages on the topic.
		log.Printf("Publishing %d messages.\n", *numToPublish)

		for i := 0; i < *numToPublish; i++ {
			res := topic.Publish(ctx, &pubsub.Message{
				Data: []byte(fmt.Sprintf("hello world %v", time.Now().UnixNano())),
			})
			// check that message was published
			_, err := r.Get(ctx)
			if err != nil {
				log.Fatal(err)
			}
			count++
		}
		log.Println("Publishing done.")
	} else {
		log.Println("Skipping publishing.")
	}

	go func() {
		for {
			log.Println("total messages read", received)
			time.Sleep(time.Second)
			if received >= *numToSubscribe {
				break
			}
		}
	}()
	if subscription != nil {
		// Pulls messages via the subscription.
		log.Printf("Subscribing %d messages.\n", *numToSubscribe)
		var mu sync.Mutex
		cctx, cancel := context.WithCancel(ctx)
		err := subscription.Receive(cctx, func(ctx context.Context, msg *pubsub.Message) {
			mu.Lock()
			defer mu.Unlock()
			received++
			//log.Printf("Got message: %q\n", string(msg.Data))
			msg.Ack()
			if received >= *numToSubscribe {
				cancel()
				return
			}
		})
		if err != nil {
			log.Fatal(err)
		}
		log.Printf("Subscription done. Received %d messages\n", received)
	} else {
		log.Println("Skipping subscription.")
	}
}
