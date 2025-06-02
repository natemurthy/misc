package main

import (
	"encoding/csv"
	"flag"
	"fmt"
	"log"
	"math"
	"sort"
	"unicode"

	// "math"
	"math/rand"
	"os"
	"strings"
	"time"

	"cloud.google.com/go/civil"
	"github.com/alpacahq/alpaca-trade-api-go/v3/alpaca"
	"github.com/alpacahq/alpaca-trade-api-go/v3/marketdata"
	"github.com/jedib0t/go-pretty/v6/table"
	"github.com/jedib0t/go-pretty/v6/text"

	//pp "github.com/k0kubun/pp/v3"
	"github.com/shopspring/decimal"
	"go.jetify.com/typeid"
	// "github.com/schollz/progressbar/v3"
)

var (
	acct           = flag.String("acct", "paper", "Select 'live' or 'paper' account")
	showCmd        = flag.String("show", "", "Show open orders, all positions, or account balance")
	orderCmd       = flag.Bool("order", false, "Submit or cancel orders to trade an asset")
	orderQty       = flag.Float64("qty", -1.0, "Quantity of shares to order, supports fractional values?")
	tradeSide      = flag.String("side", "", "The side on which to place a trade (either buy or sell)")
	testTrade      = flag.Bool("trade", false, "Test trading find fill")
	cancelOneCmd   = flag.String("cancel", "", "The ID for an individual order to cancel")
	cancelAllCmd   = flag.Bool("cancel-all", false, "If set, will cancel all orders")
	priceCmd       = flag.Bool("price", false, "Show latest SPY price")
	optionChainCmd = flag.String("option-chain", "", "Show option chain for 'call' (floor) or 'put' (ceiling)")
	symbol         = flag.String("symbol", "", "Asset symbol")
	strike         = flag.Float64("strike", -1.0, "Strike price for options floor or ceiling")
	csvFlag        = flag.Bool("csv", false, "If set along with --option-chain command will write table to CSV file")

	apiKey    = os.Getenv("APCA_API_KEY_ID")
	apiSecret = os.Getenv("APCA_API_SECRET_KEY")
)

func main() {
	flag.Parse()

	if apiKey == "" || apiSecret == "" {
		log.Fatal("Missing API credentials. Set APCA_API_KEY_ID and APCA_API_SECRET_KEY.")
	}

	baseURL := "https://paper-api.alpaca.markets"
	if *acct == "live" {
		baseURL = "https://api.alpaca.markets"
	}

	log.Printf("Using %s for %s account trading and market data RPCs\n", baseURL, *acct)

	c := apcaClient{
		apiKey:    apiKey,
		apiSecret: apiSecret,
		marketdataClient: marketdata.NewClient(marketdata.ClientOpts{
			APIKey:    apiKey,
			APISecret: apiSecret,
		}),
		tradingClient: alpaca.NewClient(alpaca.ClientOpts{
			APIKey:    apiKey,
			APISecret: apiSecret,
			BaseURL:   baseURL,
		}),
	}

	switch {
	case *showCmd == "orders":
		c.ShowAllOrders()
	case *showCmd == "balance":
		c.ShowAccountBalance()
	case *showCmd == "positions":
		c.ShowPositions()
	case *orderCmd:
		if *cancelOneCmd != "" {
			ID := *cancelOneCmd
			c.CancelOneOrder(ID)
		}
		if *cancelAllCmd {
			c.CancelAllOrders()
		}
	case *testTrade:
		// TODO move this under orderCmd when it's ready
		c.FindFill(*tradeSide, *symbol, *orderQty)
	case *priceCmd:
		s := strings.ToUpper(*symbol)
		p := c.GetLatestPrice(s)
		fmt.Printf("Latest %s price: $%.3f\n", s, p)
	case *optionChainCmd != "":
		optType := strings.ToLower(*optionChainCmd)
		if optType != "put" && optType != "call" {
			log.Fatal("Error: option-chain flag must be 'put' or 'call'")
		}
		if *strike < 1 {
			log.Fatalf("%f is an invalid strike price", *strike)
		}
		s := strings.ToUpper(*symbol)
		c.GetOptionChain(optType, s, *strike, *csvFlag)
	default:
		flag.Usage()
	}
}

type apcaClient struct {
	apiKey           string
	apiSecret        string
	marketdataClient *marketdata.Client
	tradingClient    *alpaca.Client
}

func (c *apcaClient) ShowAccountBalance() {
	account, err := c.tradingClient.GetAccount()
	if err != nil {
		log.Fatalf("Error fetching account info: %v", err)
	}
	fmt.Println()
	t := table.NewWriter()
	t.SetOutputMirror(os.Stdout)
	t.SetTitle(fmt.Sprintf("Account Balances (%s)", account.AccountNumber))
	t.AppendRow(table.Row{"Portfolio Value ($)\t", account.PortfolioValue})
	t.AppendRow(table.Row{"Cash", account.Cash})
	t.AppendRow(table.Row{"Buying Power", account.BuyingPower})
	t.Render()
}

func (c *apcaClient) ShowPositions() {
	positions, err := c.tradingClient.GetPositions()
	if err != nil {
		log.Fatalf("Error fetching account positions: %v", err)
	}
	showPositionsTable(positions)
}

func showPositionsTable(positions []alpaca.Position) {
	fmt.Println()
	t := table.NewWriter()
	t.SetOutputMirror(os.Stdout)
	headers := table.Row{"Asset", "Price", "Qty", "Market Value", "Avg Entry", "Cost Basis", "Total P/L (%)"}
	t.AppendHeader(headers)
	for _, p := range positions {
		row := table.Row{
			p.Symbol,
			fmt.Sprintf("%.4f", p.CurrentPrice.InexactFloat64()),
			p.Qty,
			fmt.Sprintf("%.4f", p.MarketValue.InexactFloat64()),
			fmt.Sprintf("%.4f", p.AvgEntryPrice.InexactFloat64()),
			fmt.Sprintf("%.4f", p.CostBasis.InexactFloat64()),
			p.UnrealizedPL,
		}
		t.AppendRow(row)
	}
	var configs []table.ColumnConfig
	for i, h := range headers {
		if h == "Price" || h == "Qty" || h == "MarketValue" || h == "Avg Entry" || h == "Cost Basis" {
			configs = append(configs, table.ColumnConfig{
				Number: i + 1, // 1-based index
				Align:  text.AlignRight,
			})
		}
	}
	t.SetColumnConfigs(configs)
	t.Render()
	fmt.Println()
}

func (c *apcaClient) ShowAllOrders() (orders []alpaca.Order) {
	orders, err := c.tradingClient.GetOrders(alpaca.GetOrdersRequest{})
	if err != nil {
		log.Fatalf("Error fetching trade orders: %v", err)
	}
	showOrdersTable(orders)
	return orders
}

func showOrdersTable(orders []alpaca.Order) {
	fmt.Println()
	t := table.NewWriter()
	t.SetOutputMirror(os.Stdout)
	headers := table.Row{"ID", "Side", "Symbol", "Qty", "Order Type", "Status"}
	t.AppendHeader(headers)
	for _, o := range orders {
		row := table.Row{
			o.ID,
			strings.ToUpper(string(o.Side)),
			o.Symbol,
			o.Qty,
			fmt.Sprintf("%s @ %v", o.Type, o.LimitPrice),
			o.Status,
		}
		t.AppendRow(row)
	}
	t.Render()
	fmt.Println()
}

func (c *apcaClient) CancelOneOrder(orderID string) {
	log.Printf("Cancelling order %s", orderID)
	if err := c.tradingClient.CancelOrder(orderID); err != nil {
		log.Fatalf("Error cancelling order: %v", err)
	}
	co, err := c.tradingClient.GetOrder(orderID)
	if err != nil {
		log.Fatalf("Error fetching cancelled order: %v", err)
	}
	showOrdersTable([]alpaca.Order{*co})
}

func (c *apcaClient) CancelAllOrders() {
	log.Println("Cancelling all orders")
	ordersToCancel, err := c.tradingClient.GetOrders(alpaca.GetOrdersRequest{})
	if err != nil {
		log.Fatalf("Error fetching trade orders: %v", err)
	}
	if len(ordersToCancel) < 1 {
		log.Println("There are no unfilled orders to cancel")
		return
	}
	if err := c.tradingClient.CancelAllOrders(); err != nil {
		log.Fatalf("Error fetching account orders: %v", err)
	}
	var cancelledOrders []alpaca.Order
	for _, o := range ordersToCancel {
		co, err := c.tradingClient.GetOrder(o.ID)
		if err != nil {
			log.Fatal("Unable to show updated order statuses")
		}
		cancelledOrders = append(cancelledOrders, *co)
	}
	showOrdersTable(cancelledOrders)
	log.Println("All unfilled orders have been cancelled")

}

func (c *apcaClient) FindFill(tradeSide string, symbol string, qty float64) {
	if tradeSide != "buy" && tradeSide != "sell" {
		log.Fatalf("Side '%s' is invalid, must be one of 'buy' or 'sell'", tradeSide)
		return
	}
	log.Printf("Finding fill price to %s %s (qty:%0.2f)", tradeSide, symbol, qty)
	// Get latest quote (for bid/ask prices)
	quote, err := c.marketdataClient.GetLatestQuote(symbol, marketdata.GetLatestQuoteRequest{})
	if err != nil {
		log.Fatalf("Failed to get latest trade: %v", err)
	}
	log.Printf("Latest quote for %s (bid: %.2f, ask %.2f)", symbol, quote.BidPrice, quote.AskPrice)

	var limitPrice float64

	// TODO use bid/ask spread to determine initial limit price
	switch tradeSide {
	case "buy":
		lastBid := quote.BidPrice
		limitPrice = roundToCent(lastBid - 0.01)
		log.Printf("Preparing initial %s limit order of %.2f ($0.01 below last bid %.2f)", strings.ToUpper(tradeSide), limitPrice, lastBid)
	case "sell":
		lastAsk := quote.AskPrice
		limitPrice = roundToCent(lastAsk + 0.01)
		log.Printf("Preparing initial %s limit order of %.2f ($0.01 below last bid %.2f)", strings.ToUpper(tradeSide), limitPrice, lastAsk)
	}

	// Setup ticker and control channel
	ticker := time.NewTicker(randomResubmitWait())
	defer ticker.Stop()
	done := make(chan bool)

	side := alpaca.Side(tradeSide) // buy or sell order

	decimalQty := decimal.NewFromFloat(qty)
	orderReq := alpaca.PlaceOrderRequest{
		Symbol:        symbol,
		Qty:           &decimalQty,
		Side:          side,
		Type:          alpaca.Limit,
		LimitPrice:    alpaca.RoundLimitPrice(decimal.NewFromFloat(limitPrice), side),
		TimeInForce:   alpaca.GTC, // GTX not (yet) supported
		ClientOrderID: randomOrderID(),
	}
	order, err := c.tradingClient.PlaceOrder(orderReq)
	if err != nil {
		log.Fatalf("Failed to place order %v", err)
	}

	log.Printf("Initial limit order placed to %s (orderID: %s)", side, order.ID)

	currentOrderID := order.ID

	// Goroutine for price monitoring and order adjustment
	go func() {
		for range ticker.C {
			prevOrder, err := c.tradingClient.GetOrder(currentOrderID)
			if err != nil {
				log.Printf("Error checking order status: %v", err)
				continue
			}

			if prevOrder.Status == "filled" {
				log.Printf("Order (%s) filled @ %v!\n", currentOrderID, prevOrder.LimitPrice)
				done <- true
				return
			}

			_ = c.tradingClient.CancelOrder(prevOrder.ID)
			switch tradeSide {
			case "buy":
				limitPrice = roundToCent(limitPrice + 0.01)
			case "sell":
				limitPrice = roundToCent(limitPrice - 0.01)
			}

			// update the original order request (not goroutine safe!)
			orderReq.ClientOrderID = randomOrderID()
			orderReq.LimitPrice = alpaca.RoundLimitPrice(decimal.NewFromFloat(limitPrice), side)

			newOrder, err := c.tradingClient.PlaceOrder(orderReq)
			if err != nil {
				log.Printf("Failed to resubmit order: %v", err)
				continue
			}
			currentOrderID = newOrder.ID
			log.Printf(
				"Order (prev:%s) not yet filled, resubmitted order at $%v (new:%s)",
				prevOrder.ID, newOrder.LimitPrice, newOrder.ID,
			)
		}
	}()

	<-done
	log.Println("Fill price discovery loop finished")
}

func (c *apcaClient) GetLatestPrice(s string) float64 {
	req := marketdata.GetLatestTradeRequest{}
	trade, err := c.marketdataClient.GetLatestTrade(s, req)
	if err != nil {
		log.Fatalf("Error fetching latest %s trade: %v", s, err)
	}
	return trade.Price
}

func (c *apcaClient) GetOptionChain(optionType, symbol string, strike float64, writeCsv bool) {
	if symbol == "" {
		log.Fatalln("Empty symbol")
	}
	if !isStrictAllUpper(symbol) {
		log.Fatalf("Symbol %s must be all uppercase", symbol)
	}
	var header table.Row
	var results []table.Row
	switch optionType {
	case "call":
		header, results = c.GetOptionFloor(symbol, strike)
	case "put":
		header, results = c.GetOptionCeiling(symbol, strike)
	}
	if writeCsv {
		createCsv(header, results)
	}
}

var optionChainHeader = table.Row{"Contract", "Expiration", "T-minus", "Bid", "Ask", "Last Fill", "Extrinsic", "θ", "δ", "γ", "ρ", "v", "ts"}

func formatRow(occ string, exp string, tMinus, bid, ask, fill, extrinsic, theta, delta, gamma, rho, vega float64, ts time.Time) table.Row {
	return table.Row{
		occ,
		exp,
		fmt.Sprintf("%.1f", tMinus),
		fmt.Sprintf("%.3f", bid),
		fmt.Sprintf("%.3f", ask),
		fmt.Sprintf("%.3f", fill),
		fmt.Sprintf("%.3f", extrinsic),
		fmt.Sprintf("%.4f", theta),
		fmt.Sprintf("%.4f", delta),
		fmt.Sprintf("%.4f", gamma),
		fmt.Sprintf("%.4f", rho),
		fmt.Sprintf("%.4f", vega),
		ts.Format("2006-01-02 15:04:05.000"),
	}
}

// Downloads and prints a strip of CALL options as leverage when upside momentum exists
func (c *apcaClient) GetOptionFloor(s string, targetStrike float64) (header table.Row, rows []table.Row) {

	t := table.NewWriter()
	t.SetOutputMirror(os.Stdout)
	headers := optionChainHeader
	t.AppendHeader(headers)
	t.SetTitle(fmt.Sprintf("%s : CALL option floor (Strike: $%.2f)", s, targetStrike))

	remainingFridays := getRemainingFridays()
	f := civil.DateOf(remainingFridays[4]) // at last 5 weeks ahead
	chain, err := marketdata.GetOptionChain(s, marketdata.GetOptionChainRequest{
		Type:              marketdata.Call,
		ExpirationDateGte: f,
	})
	if err != nil {
		log.Fatalf("Error fetching options chain for %s: %v", s, err)
	}

	//pp.Println(chain)

	now := time.Now()
	p := c.GetLatestPrice(s)
	intrinsic := math.Max(p-targetStrike, 0)
	fmt.Printf("\n%s last price: $%.3f (call strike: $%.2f, intrinsic value $%.2f)\n\n", s, p, targetStrike, intrinsic)

	for occ, snap := range chain {
		if snap.LatestTrade == nil || snap.LatestQuote == nil || snap.Greeks == nil {
			continue
		}
		fill := snap.LatestTrade.Price
		bid := snap.LatestQuote.BidPrice
		ask := snap.LatestQuote.AskPrice

		extrinsic := (fill - intrinsic)
		occMatch := genOccMatchKey(targetStrike) // NOTE: only for call options right now
		//pp.Println(occ, occMatch)
		if !strings.HasSuffix(occ, occMatch) {
			continue
		}
		occExp := strings.TrimSuffix(strings.TrimPrefix(occ, s), occMatch)
		expiration := fmt.Sprintf("20%s", addDashesEveryTwo(occExp))
		layout := "2006-01-02"
		future, _ := time.Parse(layout, expiration)
		tMinus := future.Sub(now).Hours() / 24
		r := formatRow(
			occ,
			expiration, tMinus,
			bid, ask, fill, extrinsic,
			snap.Greeks.Theta, snap.Greeks.Delta, snap.Greeks.Gamma, snap.Greeks.Rho, snap.Greeks.Vega,
			snap.LatestQuote.Timestamp,
		)
		rows = append(rows, r)
	}
	sort.Slice(rows, func(i, j int) bool {
		return rows[i][0].(string) < rows[j][0].(string)
	})
	t.AppendRows(rows)
	// right align all numerical values
	var configs []table.ColumnConfig
	for i := range headers {
		if i < 2 {
			continue
		}
		configs = append(configs, table.ColumnConfig{
			Number: i + 1, // 1-based index
			Align:  text.AlignRight,
		})
	}
	t.SetColumnConfigs(configs)
	t.SetStyle(table.StyleColoredCyanWhiteOnBlack)
	t.Style().Format.Header = text.FormatDefault
	t.Render()

	return headers, rows
}

// Downloads a strip of PUT options over the next 12 months for the given symbol and
// prints a table of those contracts to give a snapshot of downside protection costs
func (c *apcaClient) GetOptionCeiling(s string, targetStrike float64) (header table.Row, rows []table.Row) {
	// Create and configure the table
	t := table.NewWriter()
	t.SetOutputMirror(os.Stdout)
	headers := optionChainHeader
	t.AppendHeader(headers)
	t.SetTitle(fmt.Sprintf("%s : PUT option ceiling (Strike: $%.2f)", s, targetStrike))

	remainingFridays := getRemainingFridays()
	// bar := progressbar.NewOptions(len(remainingFridays),
	// 	progressbar.OptionSetDescription("Downloading options data"),
	// 	progressbar.OptionShowCount(),
	// 	progressbar.OptionSetWidth(26),
	// 	progressbar.OptionClearOnFinish(),
	// )
	start := remainingFridays[0]
	last := len(remainingFridays) - 1
	end := remainingFridays[last]
	chain, err := marketdata.GetOptionChain(s, marketdata.GetOptionChainRequest{
		Type:              marketdata.Put,
		ExpirationDateGte: civil.DateOf(start),
		ExpirationDateLte: civil.DateOf(end),
	})
	if err != nil {
		log.Fatalf("Error fetching options chain for %s: %v", s, err)
	}

	now := time.Now()
	p := c.GetLatestPrice(s)
	intrinsic := math.Max(targetStrike-p, 0)
	fmt.Printf("\n%s last price: $%.3f (put strike: $%.2f, intrinsic value $%.2f)\n\n", s, p, targetStrike, intrinsic)

	for _, friday := range remainingFridays {
		f := civil.DateOf(friday)
		tMinus := friday.Sub(now).Hours() / 24
		yy := fmt.Sprintf("%d", f.Year%100)
		mm := fmt.Sprintf("%02d", f.Month)
		dd := fmt.Sprintf("%02d", f.Day)
		occMatch := fmt.Sprintf("%s%s%s%sP00%d0", s, yy, mm, dd, int(math.Round(targetStrike*100))) // TODO may need genOccMatchKey?
		snap, ok := chain[occMatch]
		if ok {
			if snap.LatestTrade == nil || snap.LatestQuote == nil || snap.Greeks == nil {
				continue
			}
			fill := snap.LatestTrade.Price
			bid := snap.LatestQuote.BidPrice
			ask := snap.LatestQuote.AskPrice
			extrinsic := (fill - intrinsic)
			r := formatRow(
				occMatch,
				f.String(), tMinus,
				bid, ask, fill, extrinsic,
				snap.Greeks.Theta, snap.Greeks.Delta, snap.Greeks.Gamma, snap.Greeks.Rho, snap.Greeks.Vega,
				snap.LatestQuote.Timestamp,
			)
			rows = append(rows, r)
		}
		// bar.Add(1)
	}
	t.AppendRows(rows)
	// right align all numerical values
	var configs []table.ColumnConfig
	for i := range headers {
		if i < 2 {
			continue
		}
		configs = append(configs, table.ColumnConfig{
			Number: i + 1, // 1-based index
			Align:  text.AlignRight,
		})
	}
	t.SetColumnConfigs(configs)
	t.SetStyle(table.StyleColoredCyanWhiteOnBlack)
	t.Style().Format.Header = text.FormatDefault
	t.Render()

	return headers, rows
}

//
// A bunch of utility helper functions below
//

func genOccMatchKey(targetStrike float64) string {
	s := int(math.Round(targetStrike * 100))
	if targetStrike > 0 && targetStrike < 10 {
		return fmt.Sprintf("C0000%d0", s)
	} else if targetStrike >= 10 && targetStrike < 100 {
		return fmt.Sprintf("C000%d0", s)
	} else if targetStrike >= 100 && targetStrike < 1000 {
		return fmt.Sprintf("C00%d0", s)
	} else if targetStrike >= 1000 {
		return fmt.Sprintf("C0%d0", s)
	}
	return ""
}

// getRemainingFridays returns all remaining Friday dates in the current year
func getRemainingFridays() []time.Time {
	var fridays []time.Time

	now := time.Now()
	endOfYear := now.Add(time.Hour * 8760) // 12 months from now
	current := now

	// Find the next Friday
	daysUntilFriday := (5 - int(current.Weekday()) + 7) % 7
	if daysUntilFriday == 0 && current.Hour() < 16 {
		// If today is Friday and before market close, include today
		fridays = append(fridays, current)
	} else {
		// Move to next Friday
		current = current.AddDate(0, 0, daysUntilFriday)
	}

	// Get all Fridays until end of year
	for current.Before(endOfYear) {
		// Create a date for this Friday at market close (4:00 PM)
		fridayDate := time.Date(current.Year(), current.Month(), current.Day(), 16, 0, 0, 0, current.Location())
		fridays = append(fridays, fridayDate)

		// Move to next Friday
		current = current.AddDate(0, 0, 7)
	}

	return fridays
}

func isStrictAllUpper(s string) bool {
	if s == "" {
		return false
	}
	for _, r := range s {
		if !unicode.IsUpper(r) {
			return false
		}
	}
	return true
}

func addDashesEveryTwo(s string) string {
	runes := []rune(s)
	if len(runes)%2 != 0 {
		return s // or handle error if odd number of runes
	}

	var result string
	for i := 0; i < len(runes); i += 2 {
		pair := string(runes[i : i+2])
		if i > 0 {
			result += "-"
		}
		result += pair
	}
	return result
}

func createCsv(header table.Row, rows []table.Row) {
	// Create CSV file
	filename := "option_chain.csv"
	file, err := os.Create(filename)
	if err != nil {
		log.Fatal(err)
	}
	defer file.Close()

	writer := csv.NewWriter(file)
	defer writer.Flush()

	// Write header
	headerStr := make([]string, len(header))
	for i, val := range header {
		headerStr[i] = val.(string)
	}
	writer.Write(headerStr)

	// Write rows
	for _, row := range rows {
		rowStr := make([]string, len(row))
		for i, val := range row {
			rowStr[i] = val.(string)
		}
		writer.Write(rowStr)
	}
	fmt.Println()
	log.Printf("CSV export complete: %s", filename)
}

// generation random wait time between trade resubmissions (800 - 1200 ms)
func randomResubmitWait() time.Duration {
	min := 800
	max := 1200
	ms := rand.Intn(max-min+1) + min
	return time.Duration(ms) * time.Millisecond
}

func randomOrderID() string {
	orderID, _ := typeid.WithPrefix("order")
	return orderID.String()
}

func roundToCent(f float64) float64 {
	return float64(int(f*100+0.5)) / 100
}
