from . import db 
from flask_login import UserMixin 
#db.metadata.clear()

class customer(UserMixin, db.Model):
    __table_args__ = {'extend_existing': True} 
    def get_id(self):
           return (self.email)
    #id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100, collation='NOCASE'), primary_key=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))

class users(UserMixin, db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))

class booking_agent(UserMixin, db.Model):
    __table_args__ = {'extend_existing': True} 
    email = db.Column(db.String(100), primary_key=True)
    password = db.Column(db.String(100))
    booking_agent_id = db.Column(db.Integer, unique=True)

class airline(UserMixin, db.Model):
    __table_args__ = {'extend_existing': True} 
    def get_id(self):
       return (self.username)
    airline_name = db.Column(db.String(50), primary_key = True)

class airline_staff(UserMixin, db.Model):
    __table_args__ = {'extend_existing': True} 
    def get_id(self):
           return (self.username)
    username = db.Column(db.String(50), primary_key=True)
    password = db.Column(db.String(50))
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    date_of_birth = db.Column(db.Date)
    airline_name = db.Column(db.String(50))


class flight(UserMixin, db.Model):
    __table_args__ = {'extend_existing': True} 
    def get_id(self):
        return (self.flight_num)
    airline_name = db.Column(db.String(50))
    flight_num = db.Column(db.Integer, primary_key= True)
    departure_airport = db.Column(db.String(50))
    departure_time = db.Column(db.DateTime())
    arrival_airport = db.Column(db.String(50))
    arrival_time = db.Column(db.DateTime())
    price = db.Column(db.Numeric())
    status = db.Column(db.String(50))
    airplane_id = db.Column(db.Integer)

class airplane(UserMixin, db.Model):
    __table_args__ = {'extend_existing': True} 
    def get_id(self):
       return (self.airline_id)
    airline_name = db.Column(db.String(50), db.ForeignKey("airline.airline_name"))
    airplane_id =  db.Column(db.Integer, primary_key=True)
    seats = db.Column(db.Integer)

class airport(UserMixin, db.Model):
    __table_args__ = {'extend_existing': True} 
    def get_id(self):
       return (self.airport_name)
    airport_name = db.Column(db.String(50), primary_key = True)
    airport_city = db.Column(db.String(50))

class purchases(UserMixin, db.Model):
    __table_args__ = {'extend_existing': True} 
    def get_id(self):
       return (self.ticket_id)
    ticket_id = db.Column(db.String(11), primary_key = True)
    customer_email = db.Column(db.String(50), db.ForeignKey("customer.email"))
    booking_agent_id = db.Column(db.String(11))
    purchase_date = db.Column(db.DateTime)

class ticket(UserMixin, db.Model):
    __table_args__ = {'extend_existing': True} 
    def get_id(self):
       return (self.ticket_id)
    ticket_id = db.Column(db.String(11), primary_key=True)
    airline_name = db.Column(db.String(50), db.ForeignKey("airline.airline_name"))
    flight_num = db.Column(db.Integer, db.ForeignKey('flight.flight_num'))
