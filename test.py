import hashlib
import pandas as pd

df = pd.read_csv("registered_units.csv", index_col=0)

with open("key.txt", "r") as f:
    key = f.read()
    print(key)
    salt = str(df.loc[df["name"] == "pi_1", "salt"].iloc[0]).encode("utf-8")
    print(salt)
    result = hashlib.pbkdf2_hmac("sha256", key.encode("utf-8"), salt, 1)
    target = str(df.loc[df["name"] == "pi_1", "hash"].iloc[0]).encode("latin-1")
    print(result)
    print(target)
    if target == result:
        print("yay")
    else:
        print("sad")
        print(df.loc[df["name"] == "pi_1", "hash"][0])
