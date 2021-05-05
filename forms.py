from wtforms import Form, StringField, DateTimeField, DecimalField, TextField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length 
from wtforms.fields.html5 import DateTimeLocalField, DateField
from flask_wtf import FlaskForm

class addNewPlane(Form):
    airline_name = StringField(
        'Airline',
        [DataRequired()]
    )
    airplane_id = IntegerField(
        'Airplane Id', 
        [DataRequired()]
    )
    seats = IntegerField(
        'Seats', 
        [DataRequired()]
    )
    submit = SubmitField('Submit')


class addNewAirport(Form):
    airport_name = StringField(
        'Airport',
        [DataRequired()]
    )
    airport_city = StringField(
        'Airport City', 
        [DataRequired()]
    )
    submit = SubmitField('Submit')


class changeStatus(Form):
    flight_num = IntegerField(
        'Flight Number',
        [DataRequired()]
    )
    status = StringField(
        'New Status', 
        [DataRequired()]
    )
    submit = SubmitField('Submit')



class addNewFlight(Form):
    airline_name = StringField(
        'Airline',
        [DataRequired()]
    )
    flight_num = IntegerField(
        'Flight Number',
        [DataRequired()]
    )
    departure = StringField(
        'Departure Airport',
        [DataRequired()]
    )
    departure_time = DateTimeLocalField(
        'Departing Time',
        format='%m/%d/%y',
        validators=[DataRequired()]
    )
    arrival = StringField(
        'Arrival Airport',
        [DataRequired()]
    )
    arrival_time = DateTimeLocalField(
        'Arrival Time',
        format='%m/%d/%y',
        validators=[DataRequired()]
    )
    price = DecimalField(
        'Price', 
        [DataRequired()]
    )
    status = TextField(
        'Status',
        [DataRequired()]
    )
    airplane_id = IntegerField(
        'Airplane Id', 
        [DataRequired()]
    )
    submit = SubmitField('Submit')


class viewMoreFlights(FlaskForm):
    start_day = DateField(
        'Start date', 
        format='%m/%d/%y',
        validators=[DataRequired()]
    )
    end_day = DateField(
        'End date', 
        format='%m/%d/%y',
        validators=[DataRequired()]
    )
    origin = StringField(
        'Origin',
        [DataRequired()]
    )
    destination = StringField(
        'Destination',
        [DataRequired()]
    )
    submit = SubmitField('Submit')
