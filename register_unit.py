import pandas as pd
import os
import hashlib
import random
import string


def main():
    df = pd.read_csv("registered_units.csv", index_col=0)
    new_name = str(input("Input name of unit: "))

    if (df["name"].eq(new_name)).any():
        print(f"name {new_name} is already registered")
        confirmation = "a"
        while confirmation.upper() != "Y" and confirmation.upper() != "N":
            confirmation = input(f"Make new key for {new_name}? (y/n): ")
        if confirmation.upper() == "N":
            return
        else:
            df = df[df.loc[:, "name"] != new_name]

    new_key = "".join(random.choices(string.ascii_letters + string.digits, k=16))
    new_salt = "".join(
        random.choices(string.ascii_letters + string.digits, k=16)
    ).encode("utf-8")
    new_hash = hashlib.pbkdf2_hmac("sha256", new_key.encode("utf-8"), new_salt, 1)
    print("New unit registered")
    print("Please save key. It cannot be recovered")
    print(f"Name: {new_name}")
    print(f"Key: {new_key}")
    print(f"Hash: {new_hash}")
    print(f"Salt: {new_salt}")
    df.loc[len(df)] = [new_name, new_hash.decode("latin-1"), new_salt.decode("latin-1")]
    df.to_csv("registered_units.csv")


if __name__ == "__main__":
    main()
