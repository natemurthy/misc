package singleton

import (
	"sync"
)

// http://marcio.io/2015/07/singleton-pattern-in-go/

type singleton struct {
}

var instance *singleton
var once sync.Once

func GetInstance() *singleton {
	once.Do(func() {
		instance = &singleton{}
	})
	return instance
}
