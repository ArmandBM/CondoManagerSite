# Condo Manager

A small webapp that simulates a condo with residents' packages and complaints control.

## Running the server

### Requirements:
* Python 3.12–3.15 (use Python 3.14 to reproduce local validation)
* Install the project dependencies with `python -m pip install -r requirements.txt`.

### Running tests

Run `python manage.py test` after installing the dependencies. The validation
workflow uses the default Python interpreter on its runner.

### Running:

* Apply migrations
`python manage.py migrate`

* Run the server:
`python manage.py runserver`
