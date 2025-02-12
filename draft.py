import re

index_name = "crew"
if not re.match("^[a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9]$", index_name):
    print(1)
else:
    print(2)
