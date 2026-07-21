"""
Simple test for anonymize_field() using a dummy twix header.

No .dat file needed. Run it with:
    python test_anon_twix.py
"""
import re

from anon_twix import anonymize_field
from check_fields import FIELDS, extract_region, contains_data

# A dummy hdr_str fragment with the field layouts seen in real VD/VE data.
DUMMY_HEADER = (
    '<ParamString."PatientID">           { "70123456" }\n'
    '<ParamString."PatientBirthDay">     { "19850312" }\n'
    '<ParamLong."PatientSex">            { 1 }\n'
    '<ParamString."tPatientName">        { "Doe^Jane" }\n'
    '<ParamString."PatientLOID">         { "4.0.100000001" }\n'
    '<ParamString."InstitutionName">     { "Example Hospital" }\n'
    '<ParamString."InstitutionAddress">  { "Example Street 1,Example City,XY,CH,1234" }\n'
    '<ParamString."DeviceSerialNumber">  { "123456" }\n'
    '<ParamString."tStudyDescription">   {  }\n'
    '<ParamString."ParentUid">           { }\n'
    '<ParamLong."lPatientSex">           { 1 }\n'
    '<ParamDouble."flPatientHeight">     { <Unit> "[mm]" <Precision> 6 1750.000000 }\n'
    '<ParamDouble."flUsedPatientWeight"> { <Precision> 6 68.000000 }\n'
    '<ParamDouble."flPatientAge">        { <Precision> 6 35.000000 }\n'
)

# Values that must not survive anonymization.
SECRETS = ['70123456', '19850312', 'Doe^Jane', '4.0.100000001',
           'Example Hospital', 'Example Street', '123456',
           '1750.000000', '68.000000', '35.000000']


def anonymize_header(header):
    raw = header.encode('latin-1')
    for field in FIELDS:
        raw = anonymize_field(raw, field)
    return raw.decode('latin-1')


def main():
    out = anonymize_header(DUMMY_HEADER)
    failures = []

    # 1. byte length must not change (twix stores header offsets)
    if len(out) != len(DUMMY_HEADER):
        failures.append(f"length changed: {len(DUMMY_HEADER)} -> {len(out)}")

    # 2. no original value may survive
    for secret in SECRETS:
        if secret in out:
            failures.append(f"value still present: {secret}")

    # 3. structure tags and the unit label must be preserved
    for keep in ['<Unit> "[mm]"', '<Precision> 6']:
        if keep not in out:
            failures.append(f"structure lost: {keep}")

    # 4. empty fields stay untouched
    for empty in ['<ParamString."tStudyDescription">   {  }',
                  '<ParamString."ParentUid">           { }']:
        if empty not in out:
            failures.append(f"empty field changed: {empty}")

    # 5. check_fields must report every field as clean
    print("field                after anonymization")
    print("-" * 70)
    for field in FIELDS:
        region = extract_region(out, field)
        if region is None:
            continue
        leftover = contains_data(region)
        if leftover:
            failures.append(f"{field} still flagged as DATA> ({leftover})")
        mark = "DATA>" if leftover else "ok   "
        print(f"{mark} {field:20} {re.sub(r'[ ]+', ' ', region)}")

    print()
    if failures:
        print(f"FAILED ({len(failures)}):")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print("All checks passed.")


if __name__ == '__main__':
    main()
