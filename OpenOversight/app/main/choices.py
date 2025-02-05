from us import states


# Choices are a list of (value, label) tuples
SUFFIX_CHOICES = [
    ("", "-"),
    ("Jr", "Jr"),
    ("Sr", "Sr"),
    ("II", "II"),
    ("III", "III"),
    ("IV", "IV"),
    ("V", "V"),
]
RACE_CHOICES = [
    ("BLACK", "Black"),
    ("WHITE", "White"),
    ("ASIAN", "Asian"),
    ("HISPANIC", "Hispanic"),
    ("NATIVE AMERICAN", "Native American"),
    ("PACIFIC ISLANDER", "Pacific Islander"),
    ("Other", "Other"),
    ("Not Sure", "Not Sure"),
]

# For the search all form don't display Not Sure since its filtering officers
RACE_CHOICES_SEARCH = [('BLACK', 'Black'),
                ('WHITE', 'White'),
                ('ASIAN', 'Asian'),
                ('HISPANIC', 'Hispanic'),
                ('NATIVE AMERICAN', 'Native American'),
                ('PACIFIC ISLANDER', 'Pacific Islander'),
                ('Other', 'Other'), ]

GENDER_CHOICES = [
    ("Not Sure", "Not Sure"),
    ("M", "Male"),
    ("F", "Female"),
    ("Other", "Other"),
]

STATE_CHOICES = [("", "")] + [(state.abbr, state.name) for state in states.STATES]
LINK_CHOICES = [
    ("", ""),
    ("link", "Link"),
    ("video", "YouTube Video"),
    ("other_video", "Other Video"),
]
AGE_CHOICES = [(str(age), str(age)) for age in range(16, 101)]
