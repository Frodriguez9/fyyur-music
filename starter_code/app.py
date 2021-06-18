'''
    Please refer to the README file for instructions
    about how to run this app locally using a postgres db
'''


# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#


import json
import dateutil.parser
import babel
from flask import (
    Flask,
    render_template,
    request,
    Response,
    flash,
    redirect,
    url_for,
    abort
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm, CSRFProtect
from forms import *
from flask_migrate import Migrate
import sys
from models import (
    db,
    User_genre,
    Users,
    Genres,
    Venues,
    Artists,
    Shows
)


# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
csrf = CSRFProtect(app)
migrate = Migrate(app, db)


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


todays_datetime = datetime(datetime.today().year,
                           datetime.today().month,
                           datetime.today().day)


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

# ----------------------------------------------------------------------------#
# Supporting Functions. By @Frodriguez9 (GitHub)
# ----------------------------------------------------------------------------#


def populate_genres_table():
    genres = ['Alternative', 'Blues', 'Classical', 'Country', 'Electronic',
              'Folk', 'Funk', 'HipHop', 'HeavyMetal', 'Instrumental',
              'Jazz', 'MusicalTheatre', 'Pop', 'Punk', 'RB', 'Reggae',
              'RocknRoll', 'Soul', 'Other']

    for g in genres:
        new_genre = Genres(name=g)
        db.session.add(new_genre)

    db.session.commit()
    db.session.close()


def roll_back_db_session():
    db.session.rollback()
    print("EXCEPTION DETECTED")
    print(sys.exc_info())  # can provide usefull info for debuging
    return True  # This will set error vsariable to TRUE


def add_data_from_form(form, templete):
    '''
     This funtion requests data from a FORM to create new users.
     Called in the following routes:
     '/venues/create', methods=['POST']
     '/artists/create', methods=['POST']
     '''
    if Genres.query.count() == 0:  # Initializes the Genres table
        populate_genres_table()

    error = False
    form = form

    if not form.validate_on_submit():
        return render_template(templete,
                               form=form,
                               error=form.errors)
    else:
        is_seeking = True
        if form.is_seeking.data == 'No':
            is_seeking = False

        if isinstance(form, VenueForm):
            type = "Venue"
            new_type = Venues(address=form.address.data)

        elif isinstance(form, ArtistForm):
            type = "Artist"
            new_type = Artists()

    try:
        new_user = Users(type=type,
                         name=form.name.data,
                         city=form.city.data,
                         state=form.state.data,
                         phone=form.phone.data,
                         image_link=form.image_link.data,
                         facebook_link=form.facebook_link.data,
                         website=form.website.data,
                         is_seeking=is_seeking,
                         seeking_description=form.seeking_description.data)

        new_type.user = new_user

        user_genres = []
        genres_submition = form.genres.data  # returns a list
        for i in genres_submition:
            genre = Genres.query.filter(Genres.name == i).one()
            user_genres.append(User_genre(genre_id=genre.id))

        new_user.genres = user_genres

        db.session.add(new_user)
        db.session.commit()
    except:
        error = roll_back_db_session()
    finally:
        db.session.close()

    if error:
        return render_template(templete,
                               form=form,
                               error=type + ' could not be listed')

    else:
        flash(type + ' ' + request.form['name'] + ' was successfully listed!')
        return redirect(url_for('index'))


def delete_user(user_id):
    error = False
    try:
        Users.query.filter_by(id=user_id).delete()
        db.session.commit()
    except:
        error = roll_back_db_session()
    finally:
        db.session.close()
    if error:
        abort(400)
    else:
        flash('User successfully deleted')
        return redirect(url_for('index'))


def update_user(user_id,
                form,
                user_query,
                url_str_for_return,
                additional_query=None):
    user_id = user_id
    form = form
    user_info = user_query
    user_additional_info = additional_query

    error = False
    try:
        user_info.name = form.name.data,
        user_info.city = form.city.data,
        user_info.state = form.state.data,
        user_info.phone = form.phone.data,
        user_info.image_link = form.image_link.data,
        user_info.facebook_link = form.facebook_link.data,
        user_info.website = form.website.data,
        user_info.seeking_description = form.seeking_description.data

        if form.is_seeking.data == "Yes":
            user_info.is_seeking = True
        else:
            user_info.is_seeking = False

        old_genres = User_genre.query.filter(User_genre.user_id == user_id)\
                                     .delete()

        user_genres = []
        genres_submition = form.genres.data
        for i in genres_submition:
            genre = Genres.query.filter(Genres.name == i).one()
            user_genres.append(User_genre(genre_id=genre.id))

        user_info.genres = user_genres

        if user_info.type == 'Venue':
            user_additional_info.address = form.address.data

        db.session.commit()
    except:
        error = roll_back_db_session()
    finally:
        db.session.close()

    if error:
        pass  # 'edit' route will handle the error

    else:
        flash("User successfully updated")
        return redirect(url_for(url_str_for_return, user_id=user_id))


def build_show_info(show, venue, artist):
    show_info = {}
    show_info['venue_id'] = show.venue_id
    show_info['venue_name'] = venue.name
    show_info['artist_id'] = show.artist_id
    show_info['artist_name'] = artist.name
    show_info['artist_image_link'] = artist.image_link
    show_info['start_time'] = str(show.start_time)

    return show_info


def count_upcoming_shows(user_id):

    ''' the model Shows hold both Artist and Venue, each with a relationship
        to the Users class with a unique user id. Hance, the condition
        (or_(Shows.artist_id == user_id, Shows.venue_id == user_id)
        makes this function flexible to be used securely for both the Artist
        route and Venue route without qurying unwanted records'''

    num_of_shows = Shows.query.filter(
        or_(Shows.artist_id == user_id, Shows.venue_id == user_id),
        Shows.start_time > todays_datetime).count()

    return num_of_shows


def query_genres(user_id):
    user_genres = []
    genres = db.session.query(User_genre, Genres)\
        .outerjoin(Genres, User_genre.genre_id == Genres.id)\
        .filter(User_genre.user_id == user_id)\
        .all()

    for genre in genres:
        user_genres.append(genre[1].name)

    return user_genres


def google(user_type, template):

    term = request.form['search_term']

    query = Users.query.filter(Users.name.ilike(f'%{term}%'),
                               Users.type == user_type)

    data = []
    for user in query.all():
        dic = {}
        dic['id'] = user.id
        dic['name'] = user.name
        dic["num_upcoming_shows"] = count_upcoming_shows(user.id)
        data.append(dic)

    response = {"count": query.count(),
                "data": data}

    return render_template(template, results=response, search_term=term)


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route('/')
def index():
    latests_sign_ups = Users.query.order_by(db.desc(Users.id)).limit(10).all()

    data = []
    for user in latests_sign_ups:
        user_info = {}
        user_info['id'] = user.id
        user_info['type'] = user.type
        user_info['name'] = user.name
        user_info['image_link'] = user.image_link
        data.append(user_info)

    return render_template('pages/home.html', users=data)


# Venues
# ----------------------------------------------------------------------------#


@app.route('/venues')
def venues():
    places = Users.query.distinct(Users.city, Users.state)\
        .filter(Users.type == 'Venue').all()
    venues = Users.query.filter(Users.type == "Venue").all()
    locals = []

    for place in places:
        locals.append({
            "city": place.city,
            "state": place.state,
            "venues": [{
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": count_upcoming_shows(venue.id)
            } for venue in venues if
                venue.city == place.city and venue.state == place.state]
        })

    return render_template('pages/venues.html', areas=locals)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    return google(user_type='Venue', template='pages/search_venues.html')


@app.route('/venues/<int:user_id>')
def show_venue(user_id):
    venue = Users.query.filter(Users.id == user_id).one()

    venue_additional_info = Venues.query.\
        filter(Venues.user_id == user_id).one()

    genres_object = db.session\
        .query(Genres.name)\
        .join(User_genre, Genres.id == User_genre.genre_id)\
        .filter(User_genre.user_id == user_id).all()

    genres = []
    for g in genres_object:
        genre = g[0]
        genres.append(genre)

    '''
        ** IMPORTANT NOTE **

        Because of my models’ design, some of the necessary data
        to build a show object in the view, like ‘image_link’ and
        ‘venue/artist_name’ is not available in my Venue/Artist Class.
        They are available in the Users class, which condenses all the
        common information from both venues and artists.

        Because of this, I had to creatively think of a solution
        that would satisfy the rubric’s requirements by making a
        join query like venue/artist.shows, while keeping my current
        Models design. Otherwise, changing the models’ design to
        satisfy a couple of lines of code would make me rewrite
        the entire scrip.

        Here, you can see that from the join query venues/artist.shows
        I retract :
            venue_id
            artist_id
            start_time

        And I had to make an additional query to retract:
            name
            Image link

        Please read my submission note for additional explanation.
    '''

    past_shows = []
    upcoming_shows = []
    for show in venue_additional_info.shows:  # JOIN QUERY
        artist_info = Users.query\
            .filter(Users.id == show.artist_id).one()

        show_info = {
            "artist_id": show.artist_id,  # from join query
            "artist_name": artist_info.name,
            "artist_image_link": artist_info.image_link
            }
        if show.start_time <= todays_datetime:  # from join query
            show_info['start_time'] = str(show.start_time)
            past_shows.append(show_info)
        elif show.start_time > todays_datetime:  # from join query
            show_info['start_time'] = str(show.start_time)
            upcoming_shows.append(show_info)

    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": genres,
        "address": venue_additional_info.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "is_seeking": venue.is_seeking,
        "seeking_description": venue.seeking_description,
        "image_link": "https://images.unsplash.com/photo-"
                      "1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid="
                      "eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows)
      }
    db.session.close()
    return render_template('pages/show_venue.html', venue=data)

# Create Venue
# ----------------------------------------------------------------------------#


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    return add_data_from_form(VenueForm(), 'forms/new_venue.html')


@app.route('/venues/<venue_id>/delete', methods=['POST'])
def delete_venue(venue_id):
    return delete_user(venue_id)

# Artists
# ----------------------------------------------------------------------------#


@app.route('/artists')
def artists():
    artists_object = Users.query.filter(Users.type == 'Artist').all()

    artist = {}
    data = []

    for a in artists_object:
        artist = {}
        artist['id'] = a.id
        artist['name'] = a.name
        data.append(artist)

    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    return google(user_type='Artist', template='pages/search_artists.html')


@app.route('/artists/<int:user_id>')
def show_artist(user_id):
    artist = Users.query.filter(Users.id == user_id).one()

    genres_object = db.session.query(Genres.name)\
        .join(User_genre, Genres.id == User_genre.genre_id)\
        .filter(User_genre.user_id == user_id).all()

    genres = []
    for g in genres_object:
        genre = g[0]
        genres.append(genre)

    '''
    ** IMPORTANT NOTE **

    Because of my models’ design, some of the necessary data
    to build a show object in the view, like ‘image_link’ and
    ‘venue/artist_name’ is not available in my Venue/Artist Class.
    They are available in the Users class, which condenses all the
    common information from both venues and artists.

    Because of this, I had to creatively think of a solution
    that would satisfy the rubric’s requirements by making a
    join query like venue/artist.shows, while keeping my current
    Models design. Otherwise, changing the models’ design to
    satisfy a couple of lines of code would make me rewrite
    the entire scrip.

    Here, you can see that from the join query venues/artist.shows
    I retract :
        venue_id
        artist_id
        start_time

    And I had to make an additional query to retract:
        name
        Image link

    Please read my submission note for additional explanation.
    '''

    artist_shows = Artists.query\
        .filter(Artists.user_id == user_id).one()

    past_shows = []
    upcoming_shows = []

    for show in artist_shows.shows:  # Join query
        venue_info = Users.query\
            .filter(Users.id == show.venue_id).one()

        show_info = {"venue_id": show.venue_id,  # From join query
                     "venue_name": venue_info.name,
                     "venue_image_link": venue_info.image_link
                     }
        if show.start_time <= todays_datetime:  # From join query
            show_info['start_time'] = str(show.start_time)
            past_shows.append(show_info)

        elif show.start_time > todays_datetime:  # From join query
            show_info['start_time'] = str(show.start_time)
            upcoming_shows.append(show_info)

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "is_seeking": artist.is_seeking,
        "seeking_description": artist.seeking_description,
        "image_link": "https://images.unsplash.com/photo-1485686531765"
                      "-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOj"
                      "EyMDd9&auto=format&fit=crop&w=747&q=80",
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }
    db.session.close()  # Not sure if I have to invoke this on queries
    return render_template('pages/show_artist.html', artist=data)


# Update
# ----------------------------------------------------------------------------#


@app.route('/artists/<int:user_id>/edit', methods=['GET', 'POST'])
def edit_artist(user_id):
    form = ArtistForm()
    user_info = Users.query.filter(Users.id == user_id).one()

    genres = db.session.query(Genres)\
        .outerjoin(User_genre, Genres.id == User_genre.genre_id)\
        .filter(User_genre.user_id == user_id).all()

    artist = {"id": user_info.id,
              "name": user_info.name}

    is_seeking = ''

    if user_info.is_seeking:
        is_seeking = 'Yes'
    else:
        is_seeking = 'No'

    if request.method == 'GET':
        form = ArtistForm(obj=user_info)  # Populates the form
        form.is_seeking.data = is_seeking  # Handles boolean from db
        form.genres.data = [(g.name) for g in genres]
        # to prepopulate multiple choices

        return render_template('forms/edit_artist.html',
                               form=form, artist=artist)

    if request.method == 'POST' and form.validate_on_submit():
        return update_user(user_id, form, user_info,
                           'show_artist')

    else:
        return render_template('forms/edit_artist.html', form=form,
                               artist=artist, error=form.errors)


@app.route('/venues/<int:user_id>/edit', methods=['GET', 'POST'])
def edit_venue(user_id):
    form = VenueForm()
    user_info = Users.query.filter(Users.id == user_id).one()

    user_additional_info = Venues.query\
        .filter(Venues.user_id == user_id).one()

    genres = db.session.query(Genres)\
        .outerjoin(User_genre, Genres.id == User_genre.genre_id)\
        .filter(User_genre.user_id == user_id).all()

    venue = {"name": user_info.name,
             "id": user_info.id}

    is_seeking = ''

    if user_info.is_seeking:
        is_seeking = 'Yes'
    else:
        is_seeking = 'No'

    if request.method == 'GET':
        form = VenueForm(obj=user_info,  # populates Users class fields
                         address=user_additional_info.address)
                         # populates 'address' which is not in the
                         # Users class but in Venues class

        form.is_seeking.data = is_seeking  # handles boolean from db
        form.genres.data = [(g.name) for g in genres]
        # to prepopulate multiple choices

        return render_template('forms/edit_venue.html', form=form, venue=venue)

    if request.method == 'POST' and form.validate_on_submit():
        return update_user(user_id, form, user_info,
                           'show_venue', user_additional_info)

    else:
        return render_template('forms/edit_venue.html', form=form,
                               venue=venue, error=form.errors)

# Create Artist
# ----------------------------------------------------------------------------#


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    return add_data_from_form(ArtistForm(), 'forms/new_artist.html')


@app.route('/artists/<user_id>/delete', methods=['POST'])
def delete_artist(user_id):
    return delete_user(user_id)


# Shows
# ----------------------------------------------------------------------------#


@app.route('/shows')
def shows():
    shows = Shows.query.filter(Shows.start_time > todays_datetime)\
            .order_by(Shows.venue_id).all()

    data = []
    for show in shows:
        venue = Users.query.filter(Users.id == show.venue_id).one()
        artist = Users.query.filter(Users.id == show.artist_id).one()
        show_info = build_show_info(show, venue, artist)
        data.append(show_info)

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


# Create Show
# ----------------------------------------------------------------------------#


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    error = False
    form = ShowForm()

    if form.validate_on_submit():
        try:
            new_show = Shows(artist_id=form.artist_id.data,
                             venue_id=form.venue_id.data,
                             start_time=form.start_time.data)

            db.session.add(new_show)
            db.session.commit()
        except:
            error = roll_back_db_session()
        finally:
            db.session.close()

        if error:
            return render_template('forms/new_show.html',
                                   form=ShowForm(),
                                   error="Somthing went wrong. Make sure the "
                                         "Artist and Venue ID are correct.")
        else:
            flash('Show was successfully listed!')
            return redirect(url_for('index'))


@app.route('/shows/search', methods=["POST"])
def search_shows():
    term = request.form["search_term"].lower()
    shows = Shows.query.all()

    data = []
    for show in shows:
        venue = Users.query.filter(Users.id == show.venue_id).one()
        artist = Users.query.filter(Users.id == show.artist_id).one()
        if (term in artist.name.lower()) or (term in venue.name.lower()):
            show_info = build_show_info(show, venue, artist)
            data.append(show_info)

    result = {'term': term,
              'data': data,
              'count': len(data)}

    return render_template('pages/search_shows.html', results=result)


#  NOTE TO SELF: This route must be reworked to accomodate new
#  data modeling. The advance_search is not a requirement of
#  Udacity's project

@app.route('/search_shows_advance', methods=['GET', 'POST'])
def show_advance_search():
    form = ShowSeachForm()
    if request.method == 'GET':
        return render_template('pages/search_shows_advance.html', form=form)

    if request.method == 'POST':

        artist_submition = form.artist_name.data
        venue_submition = form.venue_name.data
        city_submition = form.city.data
        state_submition = form.state.data
        start_time_submition = form.start_time.data

        '''
            The form fields return a 'str type' even if the field
            is empty. This block convert them to None type so
            the filter conditions below can be executed
        '''

        if artist_submition == '':
            artist_submition = None
        if venue_submition == '':
            venue_submition = None
        if city_submition == '':
            city_submition = None
        if state_submition == 'State':
            state_submition = None

        # Filters input -------------------------------------------------------

        artist_filter = Shows.artist_name.ilike(f'%{artist_submition}%')
        venue_filter = Shows.venue_name.ilike(f'%{venue_submition}%')
        city_filter = Shows.city.ilike(f'{city_submition}')
        state_filter = Shows.state == state_submition
        if start_time_submition:
            start_time_filter = Shows.start_time >= start_time_submition

        filters = []
        if artist_submition:
            filters.append(artist_filter)
        if venue_submition:
            filters.append(venue_filter)
        if city_submition:
            filters.append(city_filter)
        if state_submition:
            filters.append(state_filter)
        if start_time_submition:
            filters.append(start_time_filter)

        shows = Shows.query.filter(*filters).all()

        data = []
        for show in shows:
            show_info = build_show_info(show)
            data.append(show_info)

        num_results = len(data)

        # TODO Ater submission: Try to implement an AJAX query in
        # the front end instead rendering the template
        return render_template('pages/search_shows_advance.html', form=form,
                               shows=data, count=num_results)


@app.route('/advance_user_search', methods=['GET', 'POST'])
def search_user():
    form = Advance_user_search_form()
    if request.method == 'GET':
        return render_template('pages/search_users_by_filters.html', form=form)

    if request.method == 'POST':

        city_submition = form.city.data
        state_submition = form.state.data
        type_submition = form.type.data
        genres_submition = form.genres.data

    '''
        The form fields return a 'str type' even if the field
        is empty. This block convert them to None type so
        the filter conditions below can be executed
    '''

    if city_submition == '':
        city_submition = None
    if state_submition == 'State':
        state_submition = None
    if type_submition == 'type' or type_submition == 'both':
        type_submition = None

    if genres_submition == '[]':
        genres_submition = None
    else:
        genres_selection = []
        for genre in genres_submition:
            genres_selection.append(Genres.name == genre)

    # Filters input -------------------------------------------------------

    city_filter = Users.city.ilike(f'{city_submition}')
    state_filter = Users.state == state_submition
    type_filter = Users.type == type_submition
    genres_filter = or_(*genres_selection)

    filters = []
    if city_submition:
        filters.append(city_filter)
    if state_submition:
        filters.append(state_filter)
    if type_submition:
        filters.append(type_filter)
    if genres_submition:
        filters.append(genres_filter)

    query = db.session.query(Users.id,
                             Users.name,
                             Users.type,
                             Users.image_link,
                             db.func.count(User_genre.user_id))\
        .outerjoin(User_genre, Users.id == User_genre.user_id)\
        .outerjoin(Genres, User_genre.genre_id == Genres.id)\
        .filter(*filters).group_by(Users.id).all()

    ''' The following for loop furthers filters the query.
        If the user selects genres as filter, we display only the
        artists/venues that meet exactly all genres the user selected '''

    results = []
    for data in query:
        genres_count = data[4]

        user_info = {}
        user_info['id'] = data[0]
        user_info['name'] = data[1]
        user_info['type'] = data[2]
        user_info['image_link'] = data[3]

        if genres_submition:
            if genres_count == len(genres_selection):
                results.append(user_info)
        else:  # when user does not pick any genre as a filter
            results.append(user_info)

    web_data = {'results': results,
                'results_count': len(results)}

    return render_template('pages/search_users_by_filters.html',
                           form=form,
                           data=web_data)


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s '
                  '[in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
