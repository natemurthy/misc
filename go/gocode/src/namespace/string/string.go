package string

func Reverse(s string) string {
	r := []rune(s)
	for i := 0; i<len(r)/2; i++ {
		j := len(r)-i-1
		r[i], r[j] = r[j], r[i]
	}
	return string(r)
}
