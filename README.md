# anonymize-twix

A simple tool for removing identifying metadata from Siemens raw TWIX (`.dat`) file headers, based on [twixtools](https://github.com/pehses/twixtools/).

Identifier fields (patient name, ID, institution, etc.) are blanked in place. The header's byte length is always preserved so the file re-reads cleanly: string values become `x`'s and numeric values become `0`'s.

## Installation

```
conda create -n twix python=3.11
conda activate twix
pip install twixtools

# If git is not installed, install it too
conda install git
```

## Usage

### 1. Inspect (before anonymization)

Show the current values of the target fields. Accepts a single `.dat` file or a directory (recurses for `*.dat`).

```
python check_fields.py input.dat
```

### 2. Anonymize

Blank the identifier fields. Accepts a single file or a directory; the input folder structure is mirrored into the output folder. Inputs are never modified and existing outputs are skipped, so it is safe to re-run.

```
python anonymize.py input.dat output_dir
python anonymize.py input_dir output_dir
```

### 3. Verify (after anonymization)

Re-run `check_fields.py` on the output to confirm every field is blanked. Fields still holding real data are marked `DATA>`.

```
python check_fields.py output_dir
```

To summarize a saved check log and highlight any leaked direct identifiers (name, DOB, patient ID):

```
python check_fields.py output_dir > check_log.txt
python parse_check_log.py check_log.txt
```

## Use as a module (`anon_twix`)

```python
import anon_twix

anon_twix.anonymize('input.dat', 'output.dat')
```

## Tests

A self-contained test (no `.dat` file needed):

```
python test_anonymize.py
```
