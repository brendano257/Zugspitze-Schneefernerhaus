import json

from collections import OrderedDict

from settings import CORE_DIR, JSON_PRIVATE_DIR

master_file = CORE_DIR / ''
second_file = CORE_DIR / ''
new_file = JSON_PRIVATE_DIR / f'filters/generated_for_review/{input("Filename for new file? (Must be unique): ")}'

with master_file.open('r') as f:
    master = json.loads(f.read())

with second_file.open('r') as f:
    second = json.loads(f.read())

print(f"The master file contains entries for {len(master)} dates.")
print(f"The second file contains entries for {len(second)} dates.")

new_only = {}

for date, compounds in second.items():
    if date in master:
        new_compounds = set(compounds) - set(master[date])  # remove any already filtered in master

        if new_compounds:  # if any new ones still exist, write new ones to that date in new_only
            new_only[date] = list(new_compounds)

    else:
        new_only[date] = compounds  # if not in master, all are new and need to be checked


if new_only:

    if new_file.exists():
        raise FileExistsError

    new_only = OrderedDict(sorted(new_only.items()))

    with new_file.open('w') as f:
        f.write(json.dumps(new_only).replace('],', '],\n'))  # dump "prettified" JSON to file
        print(f"A new file containing entries for {len(new_only)} entries was created.")
