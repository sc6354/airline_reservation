from wtforms import Form, StringField, DateTimeField, TextField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length 

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
    departure_time = DateTimeField(
        'Departing Time',
        [DataRequired()]
    )
    arrival = StringField(
        'Arrival Airport',
        [DataRequired()]
    )
    arrival_time = DateTimeField(
        'Arrival Time',
        [DataRequired()]
    )
    price = IntegerField(
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