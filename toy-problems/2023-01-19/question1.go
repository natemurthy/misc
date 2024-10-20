// Write an api that mobile client will use to get a list of debit card 
// and credit card statements ordered by most recent statements first

// mobile -> Banking service -> Statement service

// Write ListStatements endpoint in Banking service...

import (
  "tracer"
)

type BankingService struct {
  statementServiceClient *StatementService
}

func (b *BankingService) ListStatements(ctx Context, req ListStatementsRequest) (ListStatementsResponse, error) {
  tracer.Start(ctx)
  
  // TODO: wrap this in separate go routines, sychronize on a channel or a wait group
  creditCardStatements := b.statementServiceClient.GetDebitCardStatements().Statements
  debitCardStatements := b.statementServiceClient.GetCreditCardStatements().Statements
  
  allStatements := append(creditCardStatements, debitCardStatements)
  
  // apply the creation time stamp as a sortkey
  sortedStatements := allStatements.Sort()
  
  resp := ListStatementsResponse{
    // LastID: TODO: implement pagination
    // imagine the mobile client is showing a scroll feature, mobile return clients returns first 3 or 10 and so forth
    LastID: sortedStatements[len(sortedStatements)-1].LastID
    Statements: sortedStatements
  }
  resp, nil
}

// ListStatements request
// - ??
type ListStatementsRequest struct {
  UserID string
  LastID string
}

// ListStatements response
// - ??
type ListStatementsResponse struct {
  
  LastCreditCardStatementID string // "done"!
  LastDebitCardStatementID string
  
  IsDebitCardStatementsFinished bool
  IsCreditCardStatementsFinished bool
  
  Statements []Statement
}


// Statement service APIs
// ----------------------
// GetDebitCardStatements
// request
//   - lastID
//   - consumerID
//   - limit  
//   - orderBy
// response
//   - list of Statements
//   - lastID

// GetCreditCardStatements
// request
//   - lastID
//   - consumerID
//   - limit
//   - orderBy
// response
//   - list of Statements
//   - lastID



// sample query to database: `SELECT * FROM Statements WHERE id > ${last_id} AND customer_id = ${consumer_id} ORDER BY creation_timeestamp DESC LIMIT 1000`

type StatementService struct {}

type GetDebitCardStatementsResponse struct {
  Statements []Statement,
  LastID int64
}

func (s *StatementService) GetDebitCardStatements(req GetDebitCardStatementsRequest) GetDebitCardStatementsResponse {
  // assume this returns with orderBy = CreationTimestamp (with the most recent provided first)
  // assume that the 
  // assume that the limit is 100
  return GetDebitCardStatementsResponse{
    Statements: []Statements{
      LastID: "pg_1", // pagenation ID, for fetching next set of statements 
      Statement{
        ID: "st_1",
        CreationTimeestamp: 1000,
        Content: "st_1.pdf",
      },
      Statement{
        ID: "st_2",
        CreationTimeestamp: 2000,
        Content: "st_2.pdf",
      },
    }
  }
} 

func (s *StatementService) GetCreditCardStatements(req GetCreditCardStatementsRequest) GetCreditCardStatementsResponse {
  // assume this returns with orderBy = CreationTimestamp (with the most recent provided first)
  // assume that the limit is 100
  return GetCreditCardStatementsResponse{
    Statements: []Statements{
      LastID: "pg_1", // pagenation ID, for fetching next set of staetments 
      Statement{
        ID: "st_3",
        CreationTimeestamp: 1800,
        Content: "st_3.pdf",
      },
      Statement{
        ID: "st_4",
        CreationTimeestamp: 2800,
        Content: "st_4.pdf",
      },
    }
  }
} 

type Statement struct {
  ID string
  CreationTimestamp int64
  Content string
}

