from coinbase.wallet.client import Client
import os

client = Client(os.environ['API_KEY'], os.environ['API_SECRET'], api_version='2017-08-07')

accounts = client.get_accounts()

for account in accounts.data:
    balance = account.balance
    print("%s: %s %s" % (account.name, balance.amount, balance.currency))
    print(account.get_transactions())

primary_account = client.get_primary_account()
print(primary_account)
