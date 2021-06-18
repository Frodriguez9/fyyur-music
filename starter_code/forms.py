from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SelectField,
    SelectMultipleField,
    DateTimeField
    )
from wtforms.validators import (
    DataRequired,
    AnyOf,
    URL,
    Optional,
    InputRequired
    )
from enums import (
    Genres_enum,
    States_enum,
    Seeking_enum
    )
import re


#  Disclaimer: the functions 'is_valid_phone()' and 'validate_global()'
#  where written by an unknown Udacity reviwer, who suggested that
#  I implemented them


def is_valid_phone(number):
    """ Validate phone numbers like:
    1234567890 - no space
    123.456.7890 - dot separator
    123-456-7890 - dash separator
    123 456 7890 - space separator

    Patterns:
    000 = [0-9]{3}
    0000 = [0-9]{4}
    -.  = ?[-. ]

    Note: (? = optional) - Learn more: https://regex101.com/
    """
    regex = re.compile('^\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})$')
    return regex.match(number)


def validate_global(self):  # Custom validation
    rv = FlaskForm.validate(self)
    if not rv:
        return False
    if not is_valid_phone(self.phone.data):
        self.phone.errors.append('Invalid phone.')
        return False
    if not set(self.genres.data).issubset(dict(Genres_enum.choices()).keys()):
        self.genres.errors.append('Invalid genres.')
        return False
    if self.state.data not in dict(States_enum.choices()).keys():
        self.state.errors.append('Invalid state.')
        return False
    # if pass validation
    return True


class ShowForm(FlaskForm):
    artist_id = StringField(
        'artist_id', validators=[DataRequired()]
    )
    venue_id = StringField(
        'venue_id', validators=[DataRequired()]
    )
    start_time = DateTimeField(
        'start_time',
        validators=[DataRequired()],
        default=datetime.today()
    )


class VenueForm(FlaskForm):
    name = StringField(
        'name', validators=[DataRequired()]
    )
    city = StringField(
        'city', validators=[DataRequired()]
    )
    state = SelectField(
        'state', validators=[DataRequired()],
        choices=States_enum.choices()
    )
    address = StringField(
        'address', validators=[DataRequired()]
    )
    phone = StringField(
        'phone',
    )
    image_link = StringField(
        'image_link', validators=[Optional(strip_whitespace=True)]
    )
    genres = SelectMultipleField(
        'genres',
        validators=[DataRequired()],
        choices=Genres_enum.choices(),
        option_widget=None
    )
    facebook_link = StringField(
        'facebook_link', validators=[URL()]
    )

    website = StringField(
        'website', validators=[URL()]
    )

    is_seeking = SelectField(
        'seeking', validators=[DataRequired()],
        choices=Seeking_enum.choices()
    )

    seeking_description = StringField(
        'seeking_description', validators=[Optional(strip_whitespace=True)]

    )

    def validate(self):
        return validate_global(self)


class ArtistForm(FlaskForm):
    name = StringField(
        'name', validators=[DataRequired()]
    )
    city = StringField(
        'city', validators=[DataRequired()]
    )
    state = SelectField(
        'state', validators=[DataRequired()],
        choices=States_enum.choices()
    )
    phone = StringField(
        # TODO implement validation logic for state
        'phone'
    )
    image_link = StringField(
        'image_link'
    )
    genres = SelectMultipleField(
        'genres', validators=[DataRequired()],
        choices=Genres_enum.choices()
    )
    facebook_link = StringField(
        'facebook_link', validators=[URL()]
    )
    website = StringField(
        'website', validators=[URL()]
    )

    is_seeking = SelectField(
        'is_seeking', validators=[DataRequired()],
        choices=Seeking_enum.choices()
    )
    seeking_description = StringField(
        'seeking_description'
    )

    def validate(self):
        return validate_global(self)


#  Note to self: This form is not longer valid.
#  Fix accodiring to new Modeling design
#  Not requiered in Udacity's project rubric
class ShowSeachForm(FlaskForm):
    artist_name = StringField(
        'artist_name',
        validators=[Optional(strip_whitespace=True)],
        default=None,
    )

    venue_name = StringField(
        'venue_name',
        validators=[Optional(strip_whitespace=True)],
        default=None
    )

    city = StringField(
        'city',
        validators=[Optional(strip_whitespace=True)],
        default=None
    )

    state = SelectField(
        'state', choices=States_enum.choices()
    )
    start_time = DateTimeField(
        'start_time',
        default=None
    )


class Advance_user_search_form(FlaskForm):
    type = SelectField(
        'type', choices=[
                    ('type', 'User type'),
                    ('Venue', 'Venues'),
                    ('Artist', 'Artists'),
                    ('both', 'Artists & Venues')
                ]
    )
    genres = SelectMultipleField(
        'genres',
        choices=Genres_enum.choices()
    )
    city = StringField(
        'city', validators=[Optional(strip_whitespace=True)]
    )
    state = SelectField(
        'state', choices=States_enum.choices()
    )
