# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#
#  Models - Relationship Summary:

#   Many-to-Many
#     Users ---< user_genre >--- Genres
#
#   One-to-One
#     Users --- Venues --- Shows
#     Users --- Artists --- Shows
#
#
# ----------------------------------------------------------------------------#

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User_genre(db.Model):

    __tablename__ = 'user_genre'

    user_id = db.Column(db.Integer,
                        db.ForeignKey('User.id', ondelete='cascade'),
                        primary_key=True)

    genre_id = db.Column(db.Integer,
                         db.ForeignKey('Genre.id', ondelete='cascade'),
                         primary_key=True)

    def __repr__(self):
        return f'user_id: {self.user_id} genre_id {self.genre_id}'


class Users(db.Model):
    __tablename__ = 'User'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(6), nullable=False)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))  # optional to the user
    image_link = db.Column(db.String(500), default=None)
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    is_seeking = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(250))

    genres = db.relationship('User_genre',
                             backref=db.backref('user', lazy=True),
                             cascade='save-update, merge,\
                                      delete,delete-orphan',
                             passive_deletes=True)

    venue = db.relationship('Venues',
                            backref='user',
                            uselist=False,  # ensures 1 to 1 relationship
                            cascade='all, delete',
                            passive_deletes=True
                            )

    artist = db.relationship('Artists',
                             backref='user',
                             uselist=False,
                             cascade='all, delete',
                             passive_deletes=True
                             )

    def __repr__(self):
        return f'<ID: {self.id} User Type: {self.type} {self.name}>'


class Genres(db.Model):
    """ The Genres class is used as a reference table only.
    It serves as child table in the many-to-many relationship:

    Users--< user_genre >--Genres

    This allow for advanve searches such as 'the list of all
    Artists who play Rock music'. """
    __tablename__ = 'Genre'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)
    users = db.relationship('User_genre',
                            backref=db.backref('genre', lazy=True),
                            cascade='all, delete',
                            passive_deletes=True)

    def __repr__(self):
        return f'<id: {self.id} Genre: {self.name}'


class Venues(db.Model):
    __tablename__ = 'Venue'

    user_id = db.Column(db.Integer,
                        db.ForeignKey('User.id', ondelete='cascade'),
                        primary_key=True)
    address = db.Column(db.String(150), nullable=False)
    shows = db.relationship('Shows',
                            backref=db.backref('venue', lazy='joined'),
                            cascade='all, delete',
                            passive_deletes=True)

    def __repr__(self):
        return f'<Venue - User ID: {self.user_id} {self.address}>'


class Artists(db.Model):
    __tablename__ = 'Artist'

    user_id = db.Column(db.Integer,
                        db.ForeignKey('User.id', ondelete='cascade'),
                        primary_key=True)
    shows = db.relationship('Shows',
                            backref=db.backref('artist', lazy='joined'),
                            cascade='all, delete',
                            passive_deletes=True)

    def __repr__(self):
        return f'<Artist - User ID: {self.user_id}>'


class Shows(db.Model):
    __tablename__ = 'Show'
    id = db.Column(db.Integer, primary_key=True)

    artist_id = db.Column(db.Integer,
                          db.ForeignKey('Artist.user_id', ondelete='cascade'),
                          nullable=False)
    venue_id = db.Column(db.Integer,
                         db.ForeignKey('Venue.user_id', ondelete='cascade'),
                         nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
