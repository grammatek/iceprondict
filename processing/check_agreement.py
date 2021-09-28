# Command line script for checking agreement in the Icelandic pronunciation dictionary, which is in a tab-seperated .csv format
# Errors, discrepancies and suspicious-looking entries printed to a text file.
# The two arguments are by default 'ice_pron_dict_complete_2106.csv' and 'check_agreement_output.txt' (overwritten every time the script is run!)
# These arguments can also be specified by user like so:
# $ python check_agreement.py --PEDI_file=my_PEDI_file.csv --output_file=my_output_file.txt
# Note that this script does not overwrite anything in the .csv file which is checked. Some manual checking of the output will be required.
# For more info, see README.md

import sys
import argparse

prefixes = ['af', 'al', 'all', 'and', 'auð', 'einka', 'endur', 'fjar',
            'fjöl', 'for', 'frum', 'gagn', 'mis', 'ná', 'ó', 'sam', 'sí', 'tor', 'van', 'ör']
clusters = ['áf','ág','óf','óg','úf','úg','fld','gns','gts','fns','kts','fts','kkts','lds','llds',
          'lfr','lfs','lks','lps','lsks','lts','llts','mds','mmds','mps','nds','nnds','ngds','ngn',
          'nks','nsks','nnsks','pts','ppts','rfs','rfst','rgs','rks','rrks','rkst','rkts','rls','rmd',
          'rms','rmt','rnd','rnsk','rps','rpst','rpts','rsk','rsks','rskt','rsl','rsn','rst','rrst',
          'rsts','rts','rrts','sks','sps','stk','sts']
tf = ['true', 'false']
languages = ['IS', 'GB', 'DE', 'FR', 'IT', 'DK', 'NL', 'NO', 'SE', 'ES']
variants = ['standard_clear', 'standard_cas', 'north_clear', 'north_cas', 'northeast_clear',
       'northeast_cas', 'south_clear','south_cas', 'all']
POS = ['n', 'lo', 'so', 'fn', 'ao', 'ns', 'to', 'fs', 'st', 'none']
compound_attrs = ['head', 'modifier', 'both', 'none']
symbols = ['p', 'p_h', 't', 't_h', 'c', 'c_h', 'k', 'k_h', 'v', 'f', 'D', 'T', 's',
        'j', 'C', 'G', 'x', 'h', 'm', 'n', 'J', 'N', 'm_0', 'n_0', 'J_0', 'N_0', 'l',
        'l_0', 'r', 'r_0', 'I', 'I:', 'i', 'i:', 'E', 'E:', 'a', 'a:', 'Y', 'Y:',
        '9', '9:', 'u', 'u:', 'O', 'O:', 'au', 'au:', 'ou', 'ou:', 'ei', 'ei:', 'ai',
        'ai:', '9i', '9i:', 'Yi', 'Oi']
vowels = ['I', 'I:', 'i', 'i:', 'E', 'E:', 'a', 'a:', 'Y', 'Y:',
        '9', '9:', 'u', 'u:', 'O', 'O:', 'au', 'au:', 'ou', 'ou:', 'ei', 'ei:', 'ai',
        'ai:', '9i', '9i:', 'Yi', 'Oi']

word_dict = {}
identical_entries = []
identical_exc_compound = []
identical_exc_attr = []
identical_exc_prefix = []

modifiers = []
heads = []

# Lists of symbols below are for checking whether inconsistencies in pronunciation of modifiers are due to regular
# phenomena and should therefore not be listed as errors
# e.g. 'sann' pronounced [s a J] and not [s a n] in 'sanngjarnt', due to assimilation

# Dicts contain variants of same sounds, which are substituted depending on sound environment
voiced_2_unvoiced = {'D':'T', 'G':'x', 'v':'f'}
back_2_front = {'k':'c', 'N k':'J c'}

# Lists of sound categories that can impact other sounds
unvoiced_sounds = ['p_h', 't_h', 'c_h', 'k_h', 'f', 'T', 's', 'C', 'x', 'h']
vowels_and_voiced = ['I', 'I:', 'i', 'i:', 'E', 'E:', 'a', 'a:', 'Y', 'Y:',
        '9', '9:', 'u', 'u:', 'O', 'O:', 'au', 'au:', 'ou', 'ou:', 'ei', 'ei:', 'ai',
        'ai:', '9i', '9i:', 'Yi', 'Oi', 'm', 'n', 'v', 'l', 'j']
front_vowels = ['I', 'I:', 'i', 'i:', 'E', 'E:', 'ei', 'ei:', 'ai', 'ai:', 'j']

# Grouped together here, the possible sounds that can follow an aspirated plosive in Icelandic
vowels_and_vrj = ['I', 'I:', 'i', 'i:', 'E', 'E:', 'a', 'a:', 'Y', 'Y:',
        '9', '9:', 'u', 'u:', 'O', 'O:', 'au', 'au:', 'ou', 'ou:', 'ei', 'ei:', 'ai',
        'ai:', '9i', '9i:', 'Yi', 'Oi', 'v', 'j', 'r']

def is_unvoiced_variant(modifier, compound):
    mod_len = len(modifier)
    if modifier[-1] in voiced_2_unvoiced and compound.startswith(modifier[:-1] + voiced_2_unvoiced[modifier[-1]])\
            and compound[mod_len+1] in unvoiced_sounds:
                return True
    return False

def no_aspiration(modifier, compound):
    if modifier[-3:] in ['p_h', 't_h', 'k_h']:
        unasp_mod = modifier[:-3]
        mod_len = len(unasp_mod)
        if ':' in unasp_mod[-5:]:
            short_unasp_mod = unasp_mod.replace(':', '')
            short_mod_len = len(short_unasp_mod)
        if compound.startswith(unasp_mod) and compound[mod_len + 1] not in vowels_and_vrj:
            return True
        elif compound.startswith(short_unasp_mod) and compound[short_mod_len + 1] not in vowels_and_vrj:
            return True
    return False

def is_short_vowel_mod(modifier, compound):
    if ':' in modifier[-5:]:
        short_modifier = modifier.replace(':', '')
        mod_len = len(short_modifier)
        if compound.startswith(short_modifier) and compound[mod_len+1] not in vowels:
            return True
        elif is_unvoiced_variant(short_modifier, compound):
            return True
    return False

def is_short_vowel_head(head, compound):
    if ':' in head:
        short_head = head.replace(':', '')
        if compound.endswith(short_head):
            return True
        return False

def is_voiced_variant(modifier, compound):
    if modifier[-3:] in ['n_0', 'm_0', 'l_0', 'r_0']:
        voiced_modifier = modifier[:-2]
        mod_len = len(voiced_modifier)
        if compound.startswith(voiced_modifier) and compound[mod_len + 1] in vowels_and_voiced:
            return True
        return False

def is_front_variant(modifier, compound):
    print(modifier, compound)
    mod_len = len(modifier)
    if len(compound) > mod_len:
        next_sound = compound[mod_len + 1]
        if len(compound) > (mod_len + 2):
            if compound[mod_len + 2] != ' ':
                next_sound += compound[mod_len + 2]
        if modifier[-1] in back_2_front and compound.startswith(modifier[:-1] + back_2_front[modifier[-1]]) \
            and next_sound in front_vowels:
            return True
        elif modifier[-3:] in back_2_front and compound.startswith(modifier[:-3] + back_2_front[modifier[-3:]]) \
            and next_sound in front_vowels:
            return True
    return False

def no_plosive(modifier, compound):
    if modifier.endswith('N k') and compound.startswith(modifier[:-2] + ' s'):
        return True
    return False

def is_assimilated(modifier, compound):
    if ':' in modifier[-5:]:
        modifier = modifier.replace(':', '')
    split_mod = modifier.split(' ')
    split_comp = compound.split(' ')
    mod_len = len(split_mod)
    first_part = ' '.join(split_mod[:-1])
    if split_mod[-1] == 'n' and compound.startswith(first_part) and \
            split_comp[mod_len - 1] in ['N', 'J', 'N_0', 'J_0'] and \
            split_comp[mod_len] in ['k', 'c', 'k_h', 'c_h']:
        return True
    return False

def is_high_vowel(modifier, compound):
    if modifier[-1] == 'I' and compound.startswith(modifier[:-1] + 'i N'):
        return True
    elif modifier[-1] == 'I' and compound.startswith(modifier[:-1] + 'i J'):
        return True
    return False

def is_softened(modifier, compound):
    if modifier[-1] == 'k' and compound.startswith(modifier[:-1] + 'G D'):
        return True
    return False

def is_regular_pron(modifier, compound):
    if is_unvoiced_variant(modifier, compound):
        return True
    elif is_short_vowel_mod(modifier, compound):
        return True
    elif is_voiced_variant(modifier, compound):
        return True
    elif is_front_variant(modifier, compound):
        return True
    elif no_aspiration(modifier, compound):
        return True
    elif no_plosive(modifier, compound):
        return True
    elif is_assimilated(modifier, compound):
        return True
    elif is_high_vowel(modifier, compound):
        return True
    elif is_softened(modifier, compound):
        return True
    return False

def main(PEDI_file, output_file):
    prev_line = None
    org_stdout = sys.stdout
    outfile = open(output_file, 'w')
    sys.stdout = outfile
    with open(PEDI_file, 'r') as f:
        next(f)
        for line in f:
            word, sampa, pos, variant, is_compound, compound_attr, prefix, language, valid, rest = line.split('\t', 9)

            # Checking all symbols in phonetic transcription are allowable
            sampa_symbols = sampa.split(' ')
            for s in sampa_symbols:
                if s not in symbols:
                    print('Warning! Non-allowable phonetic symbol', s, 'for entry:')
                    print(line)

            # Checking options in other columns are allowable
            if pos not in POS or variant not in variants or is_compound not in tf \
                    or compound_attr not in compound_attrs \
                    or prefix not in tf or language not in languages or valid not in tf:
                print('Warning! Non-allowable option for entry:')
                print(line)

            # Storing all entries for all word forms
            line = line.split('\t', 9)
            if valid == 'true':
                if word in word_dict:
                    word_dict[word].append((line))
                else:
                    word_dict[word] = []
                    word_dict[word].append((line))

            # Checking for identical entries here:
            if line == prev_line:
                identical_entries.append(line)
            elif prev_line and line[:4] == prev_line[:4] and line[5:] == prev_line[5:]:
                identical_exc_compound.append(line)
            elif prev_line and line[:2] == prev_line[:2] and line[5] != prev_line[5]:
                identical_exc_attr.append(line)
            elif prev_line and line[:5] == prev_line[:5] and line[6:] == prev_line[6:]:
                identical_exc_prefix.append(line)
            prev_line = line

            # Collecting words marked heads and modifiers to later check agreement when used in compounds:
            if compound_attr == 'modifier':
                modifiers.append((word, sampa, variant))
            elif compound_attr == 'head':
                heads.append((word, sampa, variant))
            elif compound_attr == 'both':
                modifiers.append((word, sampa, variant))
                heads.append((word, sampa, variant))

    # Checking for missing dialectal variant entries, or entries that should be marked 'all' for PRON_VARIANT
    print('Only one entry, PRON_VARIANT not \'all\':')
    count = 0
    for word in word_dict:
        if len(word_dict[word]) == 1 and word_dict[word][0][3] != 'all':
            print(word_dict[word])
            count += 1
        elif len(word_dict[word]) == 2 and word_dict[word][0][2] != word_dict[word][1][2] and word_dict[word][0][3] != 'all':
            print(word_dict[word])
            count += 1
    if count == 0:
        print('No instances found.')

    # Checking for multiple entries for the same word form and dialectal variant
    # (these will include homographs, which should be ignored)
    print('Multiple entries (possibly homographs):')
    count = 0
    for word in word_dict:
        if len(word_dict[word]) > 1:
            variant_list = []
            sampa_list = []
            for entry in word_dict[word]:
                variant_list.append(entry[3])
                sampa_list.append(entry[1])
            if len(set(sampa_list)) > len(set(variant_list)):
                print(word_dict[word])
                count += 1
    if count == 0:
        print('No instances found.')

    # Checking for multiple entries, where one is marked 'all' for PRON_VARIANT
    print('Multiple entries, one marked \'all\':')
    count = 0
    for word in word_dict:
        if len(word_dict[word]) > 1:
            entry_list = []
            for entry in word_dict[word]:
                entry_list.append(entry[3])
            if len(set(entry_list)) > 1 and 'all' in entry_list:
                print(word_dict[word])
                count += 1
    if count == 0:
        print('No instances found.')

    # Checking for multiple entries, where none are marked 'standard_clear' for PRON_VARIANT
    print('Multiple entries, none marked \'standard clear\':')
    count = 0
    for word in word_dict:
        if len(word_dict[word]) > 1:
            entry_list = []
            for entry in word_dict[word]:
                entry_list.append(entry[3])
            if len(set(entry_list)) > 1 and 'standard_clear' not in entry_list:
                print(word_dict[word])
                count += 1
    if count == 0:
        print('No instances found.')

    # Checking for identical entries:
    print('Identical entries:')
    count = 0
    for line in identical_entries:
        print(line)
        count += 1
    if count == 0:
        print('No instances found.')

    print('Identical entries, disagreement on IS_COMPOUND:')
    count = 0
    for line in identical_exc_compound:
        print(line)
        count += 1
    if count == 0:
        print('No instances found.')

    print('Identical entries, disagreement on COMPOUND_ATTR:')
    count = 0
    for line in identical_exc_attr:
        print(line)
        count += 1
    if count == 0:
        print('No instances found.')

    print('Identical entries, disagreement on HAS_PREFIX:')
    count = 0
    for line in identical_exc_prefix:
        print(line)
        count += 1
    if count == 0:
        print('No instances found.')

    # Checking for dialectal variant entries that don't contain the phonetic features of that variant
    # e.g. a 'north_clear' entry with no aspiration marker in the phonetic transcription
    print('Suspect dialectal entries:')
    count = 0
    for word in word_dict:
        for entry in word_dict[word]:
            if 'south' in entry[3] and 'x' not in entry[1]:
                print(entry)
                count += 1
            elif 'north_' in entry[3]:
                if 't_h' not in entry[1] and 'p_h' not in entry[1] and 'k_h' not in entry[1] and 'c_h' not in entry[1]:
                    print(entry)
                    count += 1
            elif 'northeast' in entry[3]:
                if 'l' not in entry[1] and 'm' not in entry[1] and 'n' not in entry[1] \
                        and 'D' not in entry[1] and 'N' not in entry[1] and 'J' not in entry[1]:
                    print(entry)
                    count += 1
    if count == 0:
        print('No instances found.')

    # Checking that entries marked 'true' for HAS_PREFIX starts with an allowable prefix:
    print('Incorrectly marked prefixes:')
    count = 0
    for word in word_dict:
        pref_found = False
        for entry in word_dict[word]:
            if entry[6] == 'true':
                for prefix in prefixes:
                    if entry[0].startswith(prefix):
                        pref_found = True
                        break
                if pref_found == False:
                    print(entry)
                    count += 1
    if count == 0:
        print('No instances found.')

    # Checking that compound attributes are assigned the same pronunciation in every case:
    print('Compound attributes:')
    mod_error_count = 0
    head_error_count = 0
    for word in word_dict:
        for entry in word_dict[word]:
            if entry[4] == 'true':
                # First checking pronunciation of words marked as 'modifiers' when seemingly found at the start of compounds:
                for modifier in modifiers:
                    if entry[0].startswith(modifier[0]) and len(entry[0]) > (len(modifier[0]) + 1) and entry[3] == modifier[2]:
                        if not entry[1].startswith(modifier[1]):
                            if not is_regular_pron(modifier[1], entry[1]):
                                print('The modifier', modifier[0], 'not pronounced as', modifier[1], 'in entry:')
                                print(entry)
                                mod_error_count += 1
                # The same check, but for words marked as 'heads' at the end of compounds:
                for head in heads:
                    if entry[0].endswith(head[0]) and len(entry[0]) > (len(head[0]) + 1) and entry[3] == head[2]:
                        if not entry[1].endswith(head[1]) and not is_short_vowel_head(head[1], entry[1]):
                            print('The head', head[0], 'not pronounced as', head[1], 'in entry:')
                            print(entry)
                            head_error_count += 1
    if mod_error_count == 0:
        print('No discrepancies found in pronunciation of modifiers.')
    if head_error_count == 0:
        print('No discrepancies found in pronunciation of heads.')


    sys.stdout = org_stdout

parser = argparse.ArgumentParser(prog='main')
parser.add_argument('--PEDI_file', type=str, help='File in .csv format to be checked.',
                    default='ice_pron_dict_complete_2106.csv')
parser.add_argument('--output_file', type=str, help='Optionally specify a file to write output to.',
                    default='check_agreement_output.txt')
args = parser.parse_args()

if __name__ == "__main__":
    main(args.PEDI_file, args.output_file)