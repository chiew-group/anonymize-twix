"""
anon_twix 

Mark Chiew (mark.chiew@utoronto.ca)
Removes identifying metadata from twix headers

"""

import twixtools
import numpy as np
import re
import os


def anonymize(input_filename, output_filename, anon_str=None):

    if anon_str is None:
        anon_str = ['PatientID',
                    'PatientBirthDay',
                    'PatientSex',
                    'tPatientName',
                    'PatientLOID',
                    'StudyLOID',
                    'SeriesLOID',
                    'tStudyDescription',
                    'InstitutionAddress',
                    'InstitutionName',
                    'DeviceSerialNumber',
                    'CustomerId',
                    'Street',
                    'StreetNumber',
                    'ZipCode',
                    'City',
                    'District',
                    'Country',
                    'PhoneNumber',
                    'lPatientSex',
                    'tPatientName',
                    'flPatientHeight',
                    'flUsedPatientWeight',
                    'flPatientAge',
                    'PatientBirthDay',
                    'tCurrentMppsLoid',
                    'ParentLoid',
                    'ParentUid',
                    'DefaultSeriesLoid',
                    'StudyInstanceUID',
                    'PatientsName',
                    'HospitalName']

    if os.path.exists(output_filename):
        print("Output file already exists, exiting")
        return

    twix = twixtools.read_twix(input_filename, keep_syncdata=True, keep_acqend=True)

    for dataset in twix:
        
        raw_hdr = dataset['hdr_str'].tobytes()
                    
        for field in anon_str:
            raw_hdr = anonymize_field(raw_hdr, field)
    
        dataset['hdr_str'] = np.frombuffer(raw_hdr, dtype='|S1')
    
    twixtools.write_twix(twix, output_filename)


def anonymize_field(data: bytes, field_name: str, replacement_char: str = "x") -> bytes:
    s = data.decode('latin-1')

    pattern = re.compile(
        r'(<Param\w+\."{}">\s*\{{\s*)(")?([^"}}]*)(")?(\s*\}})'.format(re.escape(field_name))
    )

    def repl(match):
        prefix, open_quote, value, close_quote, suffix = match.groups()
        open_quote = open_quote or ""
        close_quote = close_quote or ""
        new_value = replacement_char * len(value)  # same length, quotes untouched
        return prefix + open_quote + new_value + close_quote + suffix

    return pattern.sub(repl, s).encode('latin-1')