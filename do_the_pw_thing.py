import random
import re
from xkcdpass import xkcd_password as xp
from string import ascii_letters, digits

special_chars = ".,:-_#+*~=?!$%&/<>"
chars = tuple(set(ascii_letters + digits + special_chars))
rand_gen = random.SystemRandom()

def generate_pw(wordfile="ger-anlx,eff-short", random_delimiters=True, numwords=6):
    wordfile = wordfile or xp.locate_wordfile()
    mywords = xp.generate_wordlist(wordfile=wordfile)

    dl = '-'
    if random_delimiters:
        dl = rand_gen.choice(special_chars)

    return xp.generate_xkcdpassword(mywords, delimiter=dl, numwords=numwords)

def ensure_ascii(pw):
    replacements = [
        ('ä', 'ae'),
        ('ö', 'oe'),
        ('ü', 'ue'),
        ('Ä', 'AE'),
        ('Ö', 'OE'),
        ('U', 'UE'),
        ('ß', 'ss'),
        ('ẞ', 'SS')
    ]

    for i in replacements:
        pw = pw.replace(i[0], i[1])

    return re.sub('[^{}]+'.format(re.escape(''.join(chars))), '_', pw)

def tmp_pass(length=128):
    return u''.join(rand_gen.choice(chars) for dummy in range(length))
