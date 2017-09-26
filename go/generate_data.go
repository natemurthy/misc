// Writing files in Go follows similar patterns to the
// ones we saw earlier for reading.

package main

import (
	"bufio"
	"flag"
	"math/rand"
	"os"
	"strconv"
	"time"
)

const End = 3600 * 24 * 365

func main() {

	var (
		deviceID       string
		installationID string
		timestamp      uint64
	)

	rand.Seed(time.Now().Unix())
	timestamp = 1422568500000000000
	flag.StringVar(&deviceID, "device", "sensorA", "device ID")
	flag.StringVar(&installationID, "installation", "123", "installation ID")

	f, _ := os.Create("influx-data-big.txt")

	defer f.Close()

	w := bufio.NewWriter(f)
	for i := 0; i < 1048576; i++ {
		tags := "device=" + deviceID + ",installation=" + installationID
		power := 10.0 * rand.Float64()
		voltage := 120.0 - rand.Float64()
		pf := 1.0 - .1*rand.Float64()
		powerStr := "power=" + strconv.FormatFloat(power, 'g', 5, 64)
		voltageStr := ",voltage=" + strconv.FormatFloat(voltage, 'g', 5, 64)
		pfStr := ",pf=" + strconv.FormatFloat(pf, 'g', 5, 64)
		str := "data," + tags + " " + powerStr + voltageStr + pfStr + " " + strconv.FormatUint(timestamp, 10) + "\n"
		w.WriteString(str)
		timestamp += 1000000000
	}

	w.Flush()
}
