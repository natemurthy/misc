package main

import (
	"encoding/json"
	"fmt"
	"os"
	"time"
)

// An exercise in (un)marshalling JSON

// http://choly.ca/post/go-json-marshalling/
type MyUser struct {
	ID          int64     `json:"id"`
	Name        string    `json:"name"`
	LastSeen    time.Time `json:"lastSeen"`
	DateOfBirth time.Time `json:"dob"`
}

func (u *MyUser) MarshalJSON() ([]byte, error) {
	type Alias MyUser
	return json.Marshal(&struct {
		LastSeen    string `json:"lastSeen"`
		DateOfBirth string `json:"dob"`
		*Alias
	}{
		LastSeen:    u.LastSeen.Format("2006-01-02 15:04:05"),
		DateOfBirth: u.DateOfBirth.Format("2006/01/02"),
		Alias:       (*Alias)(u),
	})
}

func (u *MyUser) UnmarshalJSON(data []byte) error {
	type Alias MyUser
	aux := &struct {
		LastSeen    string `json:"lastSeen"`
		DateOfBirth string `json:"dob"`
		*Alias
	}{
		Alias: (*Alias)(u),
	}
	if err := json.Unmarshal(data, &aux); err != nil {
		return err
	}
	t, err := time.Parse("2006-01-02 15:04:05", aux.LastSeen)
	if err != nil {
		return err
	}
	d, err := time.Parse("2006/01/02", aux.DateOfBirth)
	u.LastSeen = t
	u.DateOfBirth = d
	return nil
}

func main() {
	u := &MyUser{}
	js := []byte(`
	        {"id":1, 
		 "name":"Quincy", 
		 "lastSeen": "2014-11-12 18:19:20",
		 "dob": "1986/11/19"}`)
	if err := json.Unmarshal(js, u); err != nil {
		fmt.Println(err)
	}
	fmt.Println(u)

	_ = json.NewEncoder(os.Stdout).Encode(u)
}
