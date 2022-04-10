"""
Paginated API
Problem Description
A third-party API that we're using has a paginated API.  It returns results in
chunks of N.  This is implemented below on "fetch_page".
We don't think that API is very useful, and would prefer the following an implementation
where only one call to "fetch" will return a given number of results, abstracting away the
need to do pagination.
Your task will be to implement ResultFetcher.fetch()
"""

from typing import Dict
from typing import List
from typing import Optional
from typing import Union


# These numbers are for testing only and may be changed by the interviewer.
MAX_RESULTS = 103
PAGE_SIZE = 10


# External API -- Should not be modified for solution
def fetch_page(page):
    # type: (int) -> Dict[str, Union[Optional[int], List[int]]]
    """
    Return the page of results and the next page. Pages are 0 indexed.
    returns:
        {
            "results": [...],
            "next_page": 3
        }
    """
    if page * PAGE_SIZE > MAX_RESULTS:
        return {"next_page": None, "results": []}
    return {
        "next_page": page + 1,
        "results": list(
            range(page * PAGE_SIZE, min(MAX_RESULTS, (page + 1) * PAGE_SIZE))
        ),
    }


################## Implement Solution here ##################


class ResultFetcher:
    def __init__(self):
        self.curr_page = 0
        self.curr_page_results = []
        
    def fetch(self, num_results):
        # type: (int) -> List[int]
        results = []

        for _ in range(num_results):
            if len(self.curr_page_results) == 0:
                r = fetch_page(self.curr_page) 
                self.curr_page_results = r['results']
                self.curr_page += 1

            if len(self.curr_page_results) != 0:
                results.append(self.curr_page_results.pop(0))

        return results


#############################################################

def test_case(test_case, actual, expected):
    # type: (int, List[int], List[int]) -> None
    if actual == expected:
        print(f"Test Case {test_case}: SUCCESS")
    else:
        print(f"Test Case {test_case}: FAILED")
        print(f"Expected {expected}. Got {actual}")


if __name__ == "__main__":
    fetcher = ResultFetcher()
    test_case(1, fetcher.fetch(5), list(range(5)))
    test_case(2, fetcher.fetch(2), list(range(5, 7)))
    test_case(3, fetcher.fetch(7), list(range(7, 14)))
    test_case(4, fetcher.fetch(103), list(range(14, 103)))
    test_case(5, fetcher.fetch(10), [])

    fetcher = ResultFetcher()
    test_case(6, fetcher.fetch(200), list(range(103)))
