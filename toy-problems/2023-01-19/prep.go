package main

import "fmt"

// Borrowed from
// https://medium.com/@imprintpayments/how-imprint-conducts-tech-interviews-76d84dd55925

type DatabaseAccessor interface {
	Save(UserID string, decision bool) error
	Show()
}

type InMemDB struct {
	approvalDecisions map[string]bool
}

func NewDB() DatabaseAccessor {
	db := &InMemDB{
		approvalDecisions: make(map[string]bool),
	}
	return db
}

func (db *InMemDB) Save(UserID string, decision bool) error {
	db.approvalDecisions[UserID] = decision
	return nil
}

func (db *InMemDB) Show() {
	for user, decision := range db.approvalDecisions {
		if decision {
			fmt.Printf("%s : approved!\n", user)
		} else {
			fmt.Printf("%s : declined\n", user)
		}
	}
}

func saveToDB(userID string, decision bool, database DatabaseAccessor) error {
	return database.Save(userID, decision)
}

type UserProfile struct {
	UserID        string
	DOB           string
	CreditScore   int64
	MonthlyIncome float64
	MonthlyRental float64
}

func EvaluateUser(database DatabaseAccessor, user *UserProfile) error {
	if err := validateUserInput(user); err != nil {
		return err
	}
	decision := getUserApprovalDecision(user)
	return saveToDB(user.UserID, decision, database)
}

func validateUserInput(user *UserProfile) error {
	// logic to validate userInput
	return nil
}

type Rule interface {
	Validate(user *UserProfile) bool
}

type CreditScoreRule struct{}

func (r *CreditScoreRule) Validate(user *UserProfile) bool {
	return user.CreditScore > 700
}

type MonthlyIncomeRule struct{}

func (r *MonthlyIncomeRule) Validate(user *UserProfile) bool {
	return user.MonthlyIncome > 5000
}

var allRules = []Rule{&CreditScoreRule{}, &MonthlyIncomeRule{}}

func getUserApprovalDecision(user *UserProfile) bool {
	for _, rule := range allRules {
		if !rule.Validate(user) {
			return false
		}
	}
	return true
}

func getAgeFromDOB(DOB string) int {
	// logic to convert DOB string to age
	return 0
}

func main() {

	u1 := &UserProfile{
		UserID:        "user123",
		DOB:           "1987-04-29",
		CreditScore:   680,
		MonthlyIncome: 839.27,
		MonthlyRental: 355.10,
	}

	u2 := &UserProfile{
		UserID:        "user456",
		DOB:           "1993-08-22",
		CreditScore:   720,
		MonthlyIncome: 9732.21,
		MonthlyRental: 1204.30,
	}

	db := NewDB()

	EvaluateUser(db, u1)
	EvaluateUser(db, u2)

	db.Show()
}
