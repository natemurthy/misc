package main

import (
	"fmt"
	"math/rand"

	"gonum.org/v1/gonum/lapack/lapack64"
	"gonum.org/v1/gonum/mat"
	"gonum.org/v1/netlib/lapack/netlib"
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
	lapack64.Use(netlib.Implementation{})

	//wg := new(sync.WaitGroup)

	for i := 0; i < 4; i++ {
		//wg.Add(1)
		//go func() {
		//defer wg.Done()
		a := randMat(1000)
		fmt.Println(isPosDef(a))
		//}()
	}

	//wg.Wait()

}
