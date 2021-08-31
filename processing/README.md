The Python script check_agreement.py is meant to be run from the command line to check for errors, discrepancies and suspicious-looking entries in the Icelandic pronunciation dictionary. Any suspected errors are written to an output file.

The name of the file to be checked for errors and the output file that we want to write to can be specified by the user like so:
$ python check_agreement.py --PEDI_file=my_PEDI_file.csv --output_file=my_output_file.txt

If no arguments are given, the script looks for a file called 'ice_pron_dict_complete_2106.csv' in the same directory as the script and writes to a file called 'check_agreement_output.txt' (overwritten every time the script is run).

Note that this script does not overwrite anything in the .csv file which is checked for errors. Some manual checking of the output will be required, as many suspicious entries may be perfectly fine (e.g. foreign words or otherwise irregular words), see list below.

The code in the function main() is meant to weed out errors and discrepancies by looking for:

- Non-allowable symbols in the phonetic transcriptions of word forms
- Non-allowable entries in other columns (e.g. entries in the column COMPOUND_ATTR should only be 'head', 'modifier', 'both' or 'none').
- Any single entries for a word form where PRON_VARIANT is not marked 'all', suggesting a missing pronunciation variant or a mistake.
- Multiple entries for the same word form and pronunciation variant. All homographs will obviously be listed here, so manual checking for actual mistakes is required.
- Multiple entries for the same word form, where PRON_VARIANT is marked 'all' for one of them, suggesting a mistake.
- Multiple entries for the same word form, where none is marked 'standard_clear' for PRON_VARIANT, suggesting a mistake.
- Two or more identical entries
- Two or more entries that are identical, except that they differ in one of the following columns: IS_COMPOUND, COMPOUND_ATTR, HAS_PREFIX.
- Pronunciation variant entries that don't contain the phonetic features of that variant (e.g. an entry marked 'north_clear' that contains no aspiration markers in its phonetic transcription).
- Entries marked 'true' in the HAS_PREFIX column that don't start with any of the allowable prefixes (stored in the list 'prefixes' at the top of the script code)

Finally, we look for cases where compound attributes (heads and modifiers) are not pronounced the same way in each case, i.e. all entries starting with the same modifier should start with the same phonetic transcription. 
We try to filter out as many cases as possible where differences in pronunciation are due to phonological rules and therefore acceptable (e.g. the modifier 'sann' is [s a J] and not [s a n] at the start of words like 'sanngjarnt', due to assimilation.) 
However, manual checking is also required here as it is difficult to eliminate all regular cases and the script will also list some entries that appear to start/end with the same words, but actually do not (e.g. looking for compounds that start with the modifier 'óska' will also match compounds like 'óskaplega', where the modifier is 'ó' and the pronunciation different.)
