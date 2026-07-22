r"""
parse_check_log.py  --  summarize a check_fields.py log.

Focuses on DIRECT patient identifiers (name, surname, date of birth, patient ID).
Ignores fields you've accepted (age / sex / height / weight). Reports the
remaining targeted fields (institution / device serial / LOID-UID linkage keys)
separately so you can decide on them.

Usage:
    python parse_check_log.py check_log.txt
"""
import sys, re
from collections import defaultdict

# Direct patient identifiers -- any DATA> here is a real problem
CRITICAL = {'tPatientName', 'PatientsName', 'PatientID', 'PatientBirthDay'}

# Accepted by the user -- ignored entirely
IGNORED = {'PatientSex', 'lPatientSex', 'flPatientAge',
           'flPatientHeight', 'flUsedPatientWeight'}

field_line = re.compile(r'^\s*(ok|DATA>)\s+(\S+)\s+(<Param.*)$')
file_line  = re.compile(r'^====\s+(.*?)\s+====\s*$')
ds_line    = re.compile(r'^--\s+dataset\s+(\d+)\s+--\s*$')


def main():
    if len(sys.argv) < 2:
        print("usage: python parse_check_log.py <check_log.txt>")
        sys.exit(1)
    path = sys.argv[1]

    cur_file = None
    cur_ds = None
    files = []
    critical_hits = []              # (file, ds, field, value)
    other_hits = defaultdict(set)   # field -> set of files
    critical_files = set()

    with open(path, encoding='utf-8', errors='replace') as fh:
        for line in fh:
            m = file_line.match(line)
            if m:
                cur_file = m.group(1); cur_ds = None
                files.append(cur_file)
                continue
            m = ds_line.match(line)
            if m:
                cur_ds = m.group(1); continue
            m = field_line.match(line)
            if not m:
                continue
            status, field, value = m.group(1), m.group(2), m.group(3).strip()
            if status != 'DATA>':
                continue
            if field in IGNORED:
                continue
            if field in CRITICAL:
                critical_hits.append((cur_file, cur_ds, field, value))
                critical_files.add(cur_file)
            else:
                other_hits[field].add(cur_file)

    print(f"Files checked: {len(files)}")
    print()
    print("=== CRITICAL identifiers (name, surname, DOB, patient ID) ===")
    if not critical_hits:
        print("  PASS  -  no critical identifier still contains data in any file.")
    else:
        print(f"  FAIL  -  {len(critical_hits)} leak(s) across {len(critical_files)} file(s):")
        for f, ds, field, value in critical_hits:
            print(f"    {f}  [dataset {ds}]  {field}: {value}")
    print()
    print("=== Other targeted fields still containing data ===")
    print("    (institution / device serial / LOID-UID linkage keys - review per your policy)")
    if not other_hits:
        print("  none")
    else:
        for field in sorted(other_hits):
            print(f"  {field:20} in {len(other_hits[field])}/{len(files)} file(s)")
    print()
    print("Ignored by request (age / sex / height / weight): " + ", ".join(sorted(IGNORED)))


if __name__ == '__main__':
    main()
