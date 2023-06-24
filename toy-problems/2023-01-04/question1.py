class Spreadsheet():

    """
    A1 (key) -> (0,0)
    C3 (key) -> (2,2)
    """

    underlying_table = {}

    memo = {}

    def set(self, location: str, cell_value: str):
        if location in self.memo and not self._is_formula(cell_value):
            self.memo[location] = cell_value
        self.underlying_table[location] = cell_value

    def get(self, location: str) -> str:
        if location in self.underlying_table:
            expr = self.underlying_table[location]
            if self._is_formula(expr):
                if location in self.memo:
                    return str(self.memo[location])
                else:
                    res = self._reduce_expr(expr)
                    self.memo[location] = res
                    return str(res)
            else:
                return expr
        else:
            return ""

    def _is_formula(self, cell_expr: str) -> bool:
        return cell_expr.startswith("=")

    def _reduce_expr(self, cell_expr: str) -> int:
        # assume formula expressions begin with `= `
        seq = cell_expr[2:].split(" ")
        nums = []
        for e in seq:
            if e in self.underlying_table:
                nums.append(int(self.get(e)))
            elif e != "+":
                nums.append(int(e))
        #print(nums)
        return sum(nums)


"""
Test cases
"""

s = Spreadsheet()

s.set("A1", "Monday")
s.set("A2", "Tuesday")
s.set("A3", "Wednesday")

print(s.get("A1") == "Monday")
print(s.get("A2") == "Tuesday")
print(s.get("A3") == "Wednesday")

print(s.get("B4") == "")

s.set("A1", "= 10 + 23 + 2")
print(s.get("A1") == "35")

s.set("C1", "= -8 + 9 + -2")
print(s.get("C1") == "-1")

# “= D2 + E3 + 10”
s.set("D2", "10")
s.set("E3", "15")
s.set("F1", "= D2 + E3 + 10")

print(s.get("F1") == "35")

s.set("F2", "= F1 + 10")
print(s.get("F2") == "45")

s.set("F3", "= F1 + F2")
print(s.get("F3") == "80")
print(s.get("F3") == "80")

s.set("F2", "0")
print(s.get("F3"))
print(s.get("F3") == "35")

