package solution 

import "testing"

func Test(t *testing.T) {
	var testCases = []struct {
		input string
                output bool
	}{
		{"uniq", true},
		{"non-unique", false},
	}
	for _, c := range testCases {
		got := HasAllUniqueRunes(c.input)
		if got != c.output {
			t.Errorf("HasAllUniqueRunes(%q) === %t, expected %t", c.input, got, c.output)
		}
	}
}
