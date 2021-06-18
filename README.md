# Fyyur Musical

This is a full-stack application - the first project for Udacity's Full-Stack Nanodegree program.

Fyyur connects musical venues with artists. With this webapp you will be able to:

Learn about Shows, Artists, and Venues

Perform simple or advance searches by applying several levels of filters, such as musical genre, city or state, type of user, show start time, and more

See in the home page the latest venues or artists that have created a profile in Fyyur

## Instructions to run the app locally.

1. Create a postgres database with the name 'fyyur'

2. Clone this repository into your local machine.

3. Create a virtual environment in the Fyyur Music directory and activate it

4. Change directory to 'started_code'

5. Install requirements by running pip install -r requirements.txt

6. Then, run the following command on the 'started_code' directory:

    $ flask db init
    $ flask db migrate -m "Initial migration"
    $ flask db upgrade

    $ FLASK_APP=app.py flask run

 This should give you the local port where you can access Fyyur via your preferred browser!
