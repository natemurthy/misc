package main

// First I tried this:
//    https://stackoverflow.com/questions/44194842/how-to-watch-kubernetes-event-details-using-its-go-client
// But this example worked out better as far as resolving imports:
//    https://stackoverflow.com/questions/35192712/kubernetes-watch-pod-events-with-api

import (
	"flag"
	v1 "k8s.io/api/core/v1"
	meta_v1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/fields"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/cache"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"
)

func main() {
	host := flag.String("host", "https://xxx.yyy.zzz:443", "a string")
	user := flag.String("user", "kube", "a string")
	pswd := flag.String("pswd", "supersecretpw", "a string")
	flag.Parse()

	//Configure cluster info
	config := &rest.Config{Host: *host, Username: *user, Password: *pswd}
	clientset, err := kubernetes.NewForConfig(config)
	if err != nil {
		log.Fatal(err)
	}

	watchlist := cache.NewListWatchFromClient(
		clientset.Core().RESTClient(),
		"pods",
		meta_v1.NamespaceDefault, fields.Everything())

	_, controller := cache.NewInformer(
		watchlist,
		&v1.Pod{},
		0*time.Second,
		cache.ResourceEventHandlerFuncs{
			AddFunc: func(obj interface{}) {
				log.Printf("add: %s \n", obj)
			},
			DeleteFunc: func(obj interface{}) {
				log.Printf("delete: %s \n", obj)
			},
			UpdateFunc: func(oldObj, newObj interface{}) {
				log.Printf("old: %s, new: %s \n", oldObj, newObj)
			},
		},
	)
	stop := make(chan struct{})
	go controller.Run(stop)
	registerShutdownHook()
}

func registerShutdownHook() {
	sigs := make(chan os.Signal, 1)
	done := make(chan bool, 1)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		sig := <-sigs
		log.Println(sig)
		done <- true
	}()
	<-done
}
