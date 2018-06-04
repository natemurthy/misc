package main

import (
	"fmt"
	"log"
	"math/rand"
	"net/http"
	_ "net/http/pprof"
	"time"

	"gonum.org/v1/gonum/mat"
)

func randMat(d int) mat.Matrix {
	data := make([]float64, d*d)
	for i := range data {
		data[i] = rand.NormFloat64()
	}
	return mat.NewDense(d, d, data)
}

func isPosDef(x mat.Matrix) bool {
	var eig mat.Eigen
	eig.Factorize(x, false, false)
	allGreaterThanZero := true
	for _, v := range eig.Values(nil) {
		if real(v) <= 0.0 {
			allGreaterThanZero = false
			break
		}
	}
	return allGreaterThanZero
}

func main() {
	go func() {
		log.Println(http.ListenAndServe("localhost:6060", nil))
	}()

	a := randMat(1000)
	//a := mat.NewDense(3, 3, []float64{
	//2, -1, 0,
	//-1, 2, -1,
	//0, -1, 2,
	//})

	fmt.Println(isPosDef(a))

	time.Sleep(5 * time.Minute)
}
