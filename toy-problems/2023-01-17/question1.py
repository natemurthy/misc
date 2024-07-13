import random
import time

class TxnDatabase(object):
    """
    TODO: implement an in-memory database with transaction-like semantics

    My solution was missing a "snapshot": https://brandur.org/postgres-atomicity
    """

    def __init__(self):
        self.ksuid = 0
        self.underlying = {}
        self.snapshot = {} # TODO: missing from initial solution on 2023.01.17
        self.session = {}

    def set(self, key, value):
        op_id = "op_{}".format(self.ksuid)
        self.session[op_id] = {
            "ts": time.time(),
            "operation": "set",
            "key_data": key,
            "value_data": value,
        }
        if key in self.snapshot:
            self.session[op_id]["prev_data"] = self.snapshot[key]
        self.ksuid += 1
        self.__set(self.snapshot, key, value)

    def get(self, key):
        self.session["op_{}".format(self.ksuid)] = {
            "ts": time.time(),
            "operation": "get",
            "key_data": key,
        }
        self.ksuid +=1
        return self.__get(self.snapshot, key)

    def begin_t(self):
        self.snapshot = self.underlying.copy()
        self.session["session_id"] = random.randint(0,1000)

    def end_t(self):
        for k in self.session:
            if k.startswith("op_"):
                cmd = self.session[k]
                op = cmd["operation"]
                if op == "set":
                    self.__set(self.underlying, cmd["key_data"], cmd["value_data"])
        self.snapshot = {}

    def rollback(self):
        self.session = {}

    def __get(self, d, key):
        return d[key]

    def __set(self, d, key, value):
        d[key] = value


db = TxnDatabase()

try:
    db.begin_t()

    db.set('k1', 'v1')
    db.set('k2', 'v2')
    db.set('k3', '3')
    v3 = db.get('k3')
    db.set('k3', int(v3))

    print(db.snapshot)
    print(db.underlying)
except:
    print("There was an error")
    db.rollback()
finally:
    db.end_t()

print(db.snapshot)
print(db.underlying)


