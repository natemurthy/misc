package solution 

func HasAllUniqueRunes(s string) bool {
        runeCounts := make(map[rune]int)
	for _, r := range s {
		_, exists := runeCounts[r]
		if exists {
			return false
		} else {
			runeCounts[r] = 1
		}
	}
	return true
}
