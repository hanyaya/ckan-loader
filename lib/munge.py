# encoding: utf-8

# Note these functions are similar to, but separate from name/title mungers
# found in the ckanext importer. That one needs to be stable to prevent
# packages changing name on reimport, but these ones can be changed and
# improved.
import re
import os.path
from unidecode import unidecode

# Maximum length of a filename's extension (including the '.')
MAX_FILENAME_EXTENSION_LENGTH = 21

# Maximum total length of a filename (including extension)
MAX_FILENAME_TOTAL_LENGTH = 100

# Minimum total length of a filename (including extension)
MIN_FILENAME_TOTAL_LENGTH = 3
PACKAGE_NAME_MAX_LENGTH = 100
PACKAGE_NAME_MIN_LENGTH = 2

def munge_filename(filename):
    ''' Tidies a filename

    Keeps the filename extension (e.g. .csv).
    Strips off any path on the front.

    Returns a Unicode string.
    '''
    if not isinstance(filename, unicode):
        filename = decode_path(filename)

    # Ignore path
    filename = os.path.split(filename)[1]

    # Clean up
    filename = filename.lower().strip()
    filename = substitute_ascii_equivalents(filename)
    filename = re.sub(ur'[^a-zA-Z0-9_. -]', '', filename).replace(u' ', u'-')
    filename = re.sub(ur'-+', u'-', filename)

    # Enforce length constraints
    name, ext = os.path.splitext(filename)
    ext = ext[:MAX_FILENAME_EXTENSION_LENGTH]
    ext_len = len(ext)
    name = _munge_to_length(name, max(1, MIN_FILENAME_TOTAL_LENGTH - ext_len),
                            MAX_FILENAME_TOTAL_LENGTH - ext_len)
    filename = name + ext

    return filename

def munge_title_to_name(name):
    '''Munge a package title into a package name.'''
    # substitute non-ascii characters
    if isinstance(name, unicode):
        name = substitute_ascii_equivalents(name)
    # convert spaces and separators
    name = re.sub('[ .:/]', '-', name)
    # take out not-allowed characters
    name = re.sub('[^a-zA-Z0-9-_]', '', name).lower()
    # remove doubles
    name = re.sub('-+', '-', name)
    # remove leading or trailing hyphens
    name = name.strip('-')
    # if longer than max_length, keep last word if a year
    max_length = PACKAGE_NAME_MAX_LENGTH - 5
    # (make length less than max, in case we need a few for '_' chars
    # to de-clash names.)
    if len(name) > max_length:
        year_match = re.match('.*?[_-]((?:\d{2,4}[-/])?\d{2,4})$', name)
        if year_match:
            year = year_match.groups()[0]
            name = '%s-%s' % (name[:(max_length-len(year)-1)], year)
        else:
            name = name[:max_length]
    name = _munge_to_length(name, PACKAGE_NAME_MIN_LENGTH,
                            PACKAGE_NAME_MAX_LENGTH)
    return name

def _munge_to_length(string, min_length, max_length):
    '''Pad/truncates a string'''
    if len(string) < min_length:
        string += '_' * (min_length - len(string))
    if len(string) > max_length:
        string = string[:max_length]
    return string


def substitute_ascii_equivalents(text_unicode):
    # Method taken from: http://code.activestate.com/recipes/251871/
    """
    This takes a UNICODE string and replaces Latin-1 characters with something
    equivalent in 7-bit ASCII. It returns a plain ASCII string. This function
    makes a best effort to convert Latin-1 characters into ASCII equivalents.
    It does not just strip out the Latin-1 characters. All characters in the
    standard 7-bit ASCII range are preserved. In the 8th bit range all the
    Latin-1 accented letters are converted to unaccented equivalents. Most
    symbol characters are converted to something meaningful. Anything not
    converted is deleted.
    """
    char_mapping = {
        0xc0: 'A', 0xc1: 'A', 0xc2: 'A', 0xc3: 'A', 0xc4: 'A', 0xc5: 'A',
        0xc6: 'Ae', 0xc7: 'C',
        0xc8: 'E', 0xc9: 'E', 0xca: 'E', 0xcb: 'E',
        0xcc: 'I', 0xcd: 'I', 0xce: 'I', 0xcf: 'I',
        0xd0: 'Th', 0xd1: 'N',
        0xd2: 'O', 0xd3: 'O', 0xd4: 'O', 0xd5: 'O', 0xd6: 'O', 0xd8: 'O',
        0xd9: 'U', 0xda: 'U', 0xdb: 'U', 0xdc: 'U',
        0xdd: 'Y', 0xde: 'th', 0xdf: 'ss',
        0xe0: 'a', 0xe1: 'a', 0xe2: 'a', 0xe3: 'a', 0xe4: 'a', 0xe5: 'a',
        0xe6: 'ae', 0xe7: 'c',
        0xe8: 'e', 0xe9: 'e', 0xea: 'e', 0xeb: 'e',
        0xec: 'i', 0xed: 'i', 0xee: 'i', 0xef: 'i',
        0xf0: 'th', 0xf1: 'n',
        0xf2: 'o', 0xf3: 'o', 0xf4: 'o', 0xf5: 'o', 0xf6: 'o', 0xf8: 'o',
        0xf9: 'u', 0xfa: 'u', 0xfb: 'u', 0xfc: 'u',
        0xfd: 'y', 0xfe: 'th', 0xff: 'y',
        #0xa1: '!', 0xa2: '{cent}', 0xa3: '{pound}', 0xa4: '{currency}',
        #0xa5: '{yen}', 0xa6: '|', 0xa7: '{section}', 0xa8: '{umlaut}',
        #0xa9: '{C}', 0xaa: '{^a}', 0xab: '<<', 0xac: '{not}',
        #0xad: '-', 0xae: '{R}', 0xaf: '_', 0xb0: '{degrees}',
        #0xb1: '{+/-}', 0xb2: '{^2}', 0xb3: '{^3}', 0xb4:"'",
        #0xb5: '{micro}', 0xb6: '{paragraph}', 0xb7: '*', 0xb8: '{cedilla}',
        #0xb9: '{^1}', 0xba: '{^o}', 0xbb: '>>',
        #0xbc: '{1/4}', 0xbd: '{1/2}', 0xbe: '{3/4}', 0xbf: '?',
        #0xd7: '*', 0xf7: '/'
    }

    # deal with chinese
    text_unicode = slugify_chinese(text_unicode)

    r = ''
    for char in text_unicode:
        if ord(char) in char_mapping:
            r += char_mapping[ord(char)]
        elif ord(char) >= 0x80:
            pass
        else:
            r += str(char)
    return r

def slugify_chinese(string):
    # 无论用unidecode还是uuslug库，u'术' 都会被转化成'zhu'，采用了多音字里的生僻读法。
    return unidecode(string).lower().strip()