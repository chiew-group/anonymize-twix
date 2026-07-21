# -*- coding: utf-8 -*-
r"""
check_fields.py  --  inspect anonymization-target fields in Siemens twix (.dat) files.

Run it BEFORE anonymization to see the real values, and AFTER to confirm they're
blanked. Accepts a single .dat file or a directory (recurses for *.dat).

Usage:
    python check_fields.py "path\to\file.dat"
    python check_fields.py "path\to\output_dir"
"""
import sys, re, pathlib
import twixtools

# The exact field list from anon_twix.py
FIELDS = ['PatientID','PatientBirthDay','PatientSex','tPatientName','PatientLOID',
'StudyLOID','SeriesLOID','tStudyDescription','InstitutionAddress','InstitutionName',
'DeviceSerialNumber','CustomerId','Street','StreetNumber','ZipCode','City','District',
'Country','PhoneNumber','lPatientSex','flPatientHeight','flUsedPatientWeight',
'flPatientAge','tCurrentMppsLoid','ParentLoid','ParentUid','DefaultSeriesLoid',
'StudyInstanceUID','PatientsName','HospitalName']


def extract_region(s, field):
    """Return the raw '<ParamXXX."field"> { ... }' text as it appears, or None."""
    idx = s.find('."%s">' % field)
    if idx == -1:
        return None
    start = s.rfind('<Param', 0, idx)
    end = s.find('}', idx)
    if start == -1 or end == -1:
        return None
    return s[start:end + 1]


def contains_data(region):
    """Heuristic: does the value still hold real content (not just x's / structure)?"""
    inner = region[region.find('{') + 1: region.rfind('}')]
    inner = re.sub(r'<Unit>\s*"[^"]*"', '', inner)   # drop unit label, e.g. <Unit> "[mm]"
    inner = re.sub(r'<Precision>\s*\d+', '', inner)  # drop precision spec, e.g. <Precision> 6
    inner = re.sub(r'<[^>]*>', '', inner)          # drop any remaining tags
    inner = inner.replace('x', '').replace('X', '').replace('0', '')  # drop blanked runs
    inner = re.sub(r'[^A-Za-z0-9]', '', inner)       # keep only alphanumerics
    return inner  # non-empty string => still has data


def check_file(path):
    print(f"\n==== {path} ====")
    twix = twixtools.read_twix(str(path), keep_syncdata=True, keep_acqend=True)
    flagged = 0
    for di, ds in enumerate(twix):
        if not isinstance(ds, dict) or 'hdr_str' not in ds:
            continue
        s = ds['hdr_str'].tobytes().decode('latin-1')
        print(f"-- dataset {di} --")
        for field in FIELDS:
            region = extract_region(s, field)
            if region is None:
                continue
            leftover = contains_data(region)
            mark = "  DATA>" if leftover else "  ok   "
            if leftover:
                flagged += 1
            # collapse whitespace for readable one-line display
            disp = re.sub(r'\s+', ' ', region)
            print(f"{mark} {field:20} {disp}")
    print(f"-- fields still containing data: {flagged} --")
    return flagged


def main():
    if len(sys.argv) < 2:
        print("usage: python check_fields.py <file.dat | directory>")
        sys.exit(1)
    p = pathlib.Path(sys.argv[1])
    files = sorted(p.rglob('*.dat')) if p.is_dir() else [p]
    if not files:
        print("No .dat files found.")
        return
    total = 0
    for f in files:
        try:
            total += check_file(f)
        except Exception as e:
            print(f"  ERROR reading {f}: {e}")
    print(f"\n==== TOTAL fields still containing data across {len(files)} file(s): {total} ====")


if __name__ == '__main__':
    main()
