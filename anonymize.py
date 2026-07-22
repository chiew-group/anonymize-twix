r"""
anonymize.py  --  batch-anonymize Siemens twix (.dat) files.

Self-contained. Blanks a fixed set of identifier fields in each file's header
and writes a new copy, mirroring the input folder structure into the output
folder. Inputs are never modified; existing outputs are skipped (safe to
re-run/resume).

Blanking rules (byte length of the header is always preserved):
  - String params : value inside the quotes -> 'x'   (e.g. "Max" -> "xxx")
  - Numeric params: the value's digits -> '0', keeping <Unit>/<Precision> tags
                    and the decimal point, so the field stays a VALID number and
                    the file re-reads cleanly (e.g. height 1590.000000 -> 0000.000000)

Usage:
    python anonymize.py "input_dir"      "output_dir"
    python anonymize.py "one_file.dat"   "output_dir"
"""
import sys, re, os, pathlib
import numpy as np
import twixtools

# Identifier fields to blank (from anon_twix.py)
ANON_STR = ['PatientID','PatientBirthDay','PatientSex','tPatientName','PatientLOID',
'StudyLOID','SeriesLOID','tStudyDescription','InstitutionAddress','InstitutionName',
'DeviceSerialNumber','CustomerId','Street','StreetNumber','ZipCode','City','District',
'Country','PhoneNumber','lPatientSex','flPatientHeight','flUsedPatientWeight',
'flPatientAge','tCurrentMppsLoid','ParentLoid','ParentUid','DefaultSeriesLoid',
'StudyInstanceUID','PatientsName','HospitalName']

FIELD_RE = r'<Param(\w+)\."{}">\s*\{{([^}}]*)\}}'


def blank_value(param_type, interior):
    """Blank the real value inside a param's braces, preserving structure & length."""
    if param_type == 'String':
        # blank inside every quoted string with x (same length)
        return re.sub(r'"([^"]*)"',
                      lambda m: '"' + 'x' * len(m.group(1)) + '"',
                      interior)
    # numeric-like (Long/Double/Bool): zero the DIGITS of every numeric value,
    # keeping '.', sign, and the <Unit> "..." / <Precision> N tags -> stays a valid number
    return re.sub(r'(<Unit>\s*"[^"]*"|<Precision>\s*\d+)|[-+]?\d[\d.]*',
                  lambda m: m.group(1) or re.sub(r'\d', '0', m.group(0)),
                  interior)


def anonymize_field(data: bytes, field_name: str) -> bytes:
    s = data.decode('latin-1')
    pat = re.compile(FIELD_RE.format(re.escape(field_name)))
    def repl(m):
        ptype, interior = m.group(1), m.group(2)
        full = m.group(0)
        cut = full.index('{')
        return full[:cut + 1] + blank_value(ptype, interior) + '}'
    return pat.sub(repl, s).encode('latin-1')


def anonymize(input_filename, output_filename):
    if os.path.exists(output_filename):
        print("  SKIP (output exists)")
        return
    twix = twixtools.read_twix(input_filename, keep_syncdata=True, keep_acqend=True)
    for dataset in twix:
        if not isinstance(dataset, dict) or 'hdr_str' not in dataset:
            continue
        raw = dataset['hdr_str'].tobytes()
        n0 = len(raw)
        for field in ANON_STR:
            raw = anonymize_field(raw, field)
        assert len(raw) == n0, "header length changed - aborting to avoid corruption"
        dataset['hdr_str'] = np.frombuffer(raw, dtype='|S1')
    twixtools.write_twix(twix, output_filename)


def main():
    if len(sys.argv) < 3:
        print("usage: python anonymize.py <input_dir|file.dat> <output_dir>")
        sys.exit(1)
    in_path = pathlib.Path(sys.argv[1])
    out_dir = pathlib.Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)

    if in_path.is_dir():
        files = sorted(in_path.rglob('*.dat'))
        base = in_path
    else:
        files = [in_path]
        base = in_path.parent

    print(f"Found {len(files)} file(s)")
    ok = fail = 0
    for i, f in enumerate(files, 1):
        rel = f.relative_to(base)
        out = out_dir / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        print(f"[{i}/{len(files)}] {rel}")
        try:
            anonymize(str(f), str(out))
            ok += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            fail += 1
    print(f"\nDone. ok={ok} failed={fail}")
    print("Verify with:  python check_fields.py \"%s\"" % out_dir)


if __name__ == '__main__':
    main()
