from flask import Blueprint, render_template, session, request, flash, redirect, url_for, make_response
from flask_login import login_required, current_user
from . import db 
from .models import flight, purchases, ticket, airport, airplane, ticket, purchases, customer, airplane
from sqlalchemy.orm import aliased
from sqlalchemy import extract
from sqlalchemy import func
from datetime import datetime, date, timedelta   
import uuid
import shortuuid
from .forms import addNewPlane, addNewAirport, changeStatus, addNewFlight

main = Blueprint('main', __name__)

@main.route('/', methods=["POST", 'GET'])
def index():
    if request.method == 'POST':
        origin = request.form.get('departure').upper()
        destination = request.form.get('destination').upper()
        date = request.form.get('date')

        airport1 = aliased(airport, name ='origin')
        airport2 = aliased(airport, name = 'destination')

        #payments = Payment.query.filter(extract('month', Payment.due_date) >= datetime.today().month,
                #    extract('year', Payment.due_date) >= datetime.today().year,
                    #            extract('day', Payment.due_date) >= datetime.today().day).all()

        all_flights = db.session.query(flight, airport1, airport2, airplane)\
                                .outerjoin(airport1, airport1.airport_name == flight.departure_airport)\
                                .join(airport2, airport2.airport_name == flight.arrival_airport)\
                                .join(airplane, airplane.airplane_id == flight.airplane_id)\
                                .filter(flight.departure_time == date).all()

        if not all_flights:
            flash('Sorry, no flights found. Change your selection and try again.')
            return (redirect(url_for('main.index')))
        else:
            return render_template('flights.html', flights = all_flights)
        
    return render_template('index.html')


@main.route('/profile')
@login_required
#@roles_required('Customer')
def profile():
    
    today_date = date.today()
    email = "%{0}%".format(current_user.username)
    airport1 = aliased(airport, name ='origin')
    airport2 = aliased(airport, name = 'destination')

    fname = db.session.query(customer).filter(customer.email.like(email)).first()

    upcoming_flights = db.session.query(purchases, flight, ticket, airport1, airport2)\
            .filter(purchases.customer_email.like(email))\
            .join(ticket, ticket.ticket_id == purchases.ticket_id)\
            .join(flight, flight.flight_num == ticket.flight_num)\
            .outerjoin(airport1, airport1.airport_name == flight.departure_airport)\
            .join(airport2, airport2.airport_name == flight.arrival_airport)\
            .filter(flight.departure_time >= today_date).all()

    past_flights = db.session.query(purchases, flight, ticket, airport1, airport2)\
            .filter(purchases.customer_email.like(email))\
            .join(ticket, ticket.ticket_id == purchases.ticket_id)\
            .join(flight, flight.flight_num == ticket.flight_num)\
            .outerjoin(airport1, airport1.airport_name == flight.departure_airport)\
            .join(airport2, airport2.airport_name == flight.arrival_airport)\
            .filter(flight.departure_time <= today_date).all()

    # need flight, ticket, and purchases
    spending = flight.query.with_entities(func.sum(flight.price))\
                         .join(ticket, ticket.flight_num == flight.flight_num)\
                         .join(purchases, purchases.ticket_id == ticket.ticket_id)\
                         .filter(purchases.customer_email.like(email)).all()

    spending1 = db.session.query(func.month(purchases.purchase_date), func.sum(flight.price).label('monthly_total'))\
                          .join(ticket, ticket.ticket_id == purchases.ticket_id)\
                          .join(flight, flight.flight_num == ticket.flight_num)\
                          .filter(purchases.customer_email.like(email))\
                          .group_by(func.month(purchases.purchase_date)).all()

    labels = [row[0] for row in spending1]
    values = [row[1] for row in spending1]

    
    if not upcoming_flights:
        flash('Looks like you have no planned trips.')
    
    return render_template('profile.html', name = fname, email = current_user.username, 
                                           all_upcoming_flights = upcoming_flights, 
                                           all_past_flights = past_flights, 
                                           all_spending = spending[0][0], x =labels, y =values)


@main.route('/staff_home',methods=["POST", "GET"])
@login_required
def staffHome():
    new_plane_form = addNewPlane(request.form)
    airport_form = addNewAirport(request.form)
    status_form = changeStatus(request.form)
    flight_form = addNewFlight(request.form)

    if new_plane_form.validate():
        new_plane = airplane(airline_name = new_plane_form.airline_name.data, 
                             airplane_id = new_plane_form.airplane_id.data, 
                             seats= new_plane_form.seats.data)
        db.session.add(new_plane) 
        db.session.commit()
        return redirect(url_for('main.staffHome'))

    if airport_form.validate():
        new_airport = airport(airport_name = airport_form.airport_name.data, 
                             airport_city = airport_form.airport_city.data)
        db.session.add(new_airport) 
        db.session.commit()
        return redirect(url_for('main.staffHome'))

    if status_form.validate():
        db.session.query(flight).filter(flight.flight_num == status_form.flight_num.data)\
                                .update({flight.status: status_form.status.data})
        db.session.commit()
        return redirect(url_for('main.staffHome'))

    if flight_form.validate():
        new_flight= flight(airline_name = flight_form.airline_name.data,
                           flight_num = flight_form.flight_num.data,
                           departure_airport= flight_form.departure.data, 
                           departure_time =flight_form.departuare_time.data,
                           arrival_airport= flight_form.arrival.data, 
                           arrival_time =flight_form.arrival_time.data,
                           price = flight_form.price.data,
                           status = flight_form.status.data,
                           airplane_id = flight_form.airplane_id.data)
        db.session.add(new_flight) 
        db.session.commit()
        return redirect(url_for('main.staffHome'))

    
    return render_template('staffHome.html', form = new_plane_form, 
                                             form2 = airport_form,
                                             form3 = status_form,
                                             form4 = flight_form)

@main.route('/flights', methods=["POST"])
def flights():
    #id = uuid.uuid4()
    id = shortuuid.ShortUUID().random(length=20)
    airline = request.form.get('airline')
    flight = request.form.get('flight')
    issued_ticket = ticket(ticket_id = id, airline_name = airline, flight_num = flight)
    purchase = purchases(ticket_id = id, customer_email = current_user.username, purchase_date = date.today())
    db.session.add(issued_ticket)
    db.session.add(purchase)
    db.session.commit()
    return render_template('flights.html',)

