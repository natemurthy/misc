def balance_accounts(accts):
    tx = []
    needed = {}
    capabilities = {}
    
    for acct, bal in accts.items():
        if bal < 100:
            needed[acct] = abs(100-bal)
        elif bal > 100:
            capabilities[acct] = abs(bal-100)
            
    for acct, needed_amount in needed.items():
        for k, capable_amount in capabilities.items():
            if capable_amount <= 0 or needed_amount <= 0:
                continue
            diff = capable_amount - needed_amount
            if diff > 0:
                tx.append(
                    {"from": k, "to": acct, "amount": diff}
                )
                capabilities[k] -= diff
                needed[acct] -= diff
            else:
                tx.append(
                    {"from": k, "to": acct, "amount": capable_amount}
                )
                capabilities[k] -= capable_amount
                needed[acct] -= capable_amount

            needed_amount = needed[acct] 
            if needed_amount == 0:
                break
    return tx


in1 = {"AU": 100}
print(balance_accounts(in1))

in2 = {"AU": 80, "US": 140}
print(balance_accounts(in2))

in3 = {
"AU": 80,
"US": 140,
"MX": 110,
"SG": 120,
"FR": 70,
}
print(balance_accounts(in3))



            
        

"""
in1 = {"AU": 100},            out = []
in2 = {"AU": 80, "US": 140},  out = [{"from": "US", "to": "AU", "amount": 20}]
in3 = {
AU: 80
US: 140
MX: 110
SG: 120
FR: 70
}

needed = {AU: 20, FR: 30}

capability = {US: 40, MX: 10, SG: 20}
tx = [

{from: US, to: AU, amount: 20}
{from: MX, to: FR, amount: 10}
{from: SGL to: FR: amount: 20}
]


"""

# 
# Your previous Markdown content is preserved below:
# 
# At Stripe we keep track of where the money is and move money between bank accounts to make sure their balances are not below some threshold. This is for operational and regulatory reasons, e.g. we should have enough funds to pay out to our users, and we are legally required to separate our users' funds from our own. This interview question is a simplified version of a real-world problem we have here.
# 
# Let's say there are at most 500 bank accounts, some of their balances are above 100 and some are below. How do you move money between them so that they all have at least 100?
# 
# Just to be clear we are not looking for the optimal solution, but a working one.
# 
# Example input:
#   - AU: 80
#   - US: 140
#   - MX: 110
#   - SG: 120
#   - FR: 70
#  
# Output:
#   - from: US, to: AU, amount: 20  
#   - from: US, to: FR, amount: 20
#   - from: MX, to: FR, amount: 10

