from flask import Blueprint, render_template, session, request, flash, redirect, url_for, make_response
from flask_login import login_required, current_user
from . import db 
from .models import *
from sqlalchemy.orm import aliased
from sqlalchemy import extract,func, or_
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

        all_flights = db.session.query(flight, airport1, airport2, airplane)\
                                .join(airport1, airport1.airport_name == flight.departure_airport)\
                                .join(airport2, airport2.airport_name == flight.arrival_airport)\
                                .join(airplane, airplane.airplane_id == flight.airplane_id)\
                                .filter(flight.departure_time == date)\
                                .filter(or_(airport1.airport_city == origin, airport1.airport_name == origin))\
                                .filter(or_(airport2.airport_city == destination, airport2.airport_name == destination))\
                                .all()

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


    time_limit = date.today() + timedelta(days=30)
    staff_name = db.session.query(airline_staff.first_name).filter(airline_staff.username==current_user.username).first()
    airline = db.session.query(airline_staff.airline_name).filter(airline_staff.username==current_user.username).first()
    airport1 = aliased(airport, name ='origin')
    airport2 = aliased(airport, name = 'destination')

    flightsIn30Days = db.session.query(flight, airport1, airport2)\
                                .join(airport1, airport1.airport_name == flight.departure_airport)\
                                .join(airport2, airport2.airport_name == flight.arrival_airport)\
                                .filter(flight.departure_time >= date.today())\
                                .filter(flight.departure_time <= time_limit).all()


    if new_plane_form.validate():
        new_plane = airplane(airline_name = new_plane_form.airline_name.data, 
                             airplane_id = new_plane_form.airplane_id.data, 
                             seats= new_plane_form.seats.data)
        db.session.add(new_plane) 
        db.session.commit()
        flash('New Plane Succefully Added.')
        return redirect(url_for('main.staffHome'))

    if airport_form.validate():
        new_airport = airport(airport_name = airport_form.airport_name.data, 
                             airport_city = airport_form.airport_city.data)
        db.session.add(new_airport) 
        db.session.commit()
        flash('New Airport Successfully Added.')
        return redirect(url_for('main.staffHome'))

    if status_form.validate():
        db.session.query(flight).filter(flight.flight_num == status_form.flight_num.data)\
                                .update({flight.status: status_form.status.data})
        db.session.commit()
        flash('Flight Status Succefully Updated.')
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
        db.session.flush()
        db.session.commit()
        flash('New Flight Successfully Added.')
        return redirect(url_for('main.staffHome'))
    
    return render_template('staffHome.html', form = new_plane_form, 
                                             form2 = airport_form,
                                             form3 = status_form,
                                             form4 = flight_form,
                                             name = staff_name[0],
                                             airline = airline[0], 
                                             all_upcoming_flights = flightsIn30Days)


@main.route('/agent_home',methods=["POST", "GET"])
@login_required
def agentHome():
    today_date = date.today()
    email = "%{0}%".format(current_user.username)
    airport1 = aliased(airport, name ='origin')
    airport2 = aliased(airport, name = 'destination')

    fname = db.session.query(booking_agent).filter(booking_agent.email.like(email)).first()
    agent_id = db.session.query(booking_agent.booking_agent_id).filter(booking_agent.email.like(email)).first()

    upcoming_flights = db.session.query(purchases, customer, ticket, flight, airport1, airport2)\
            .filter(purchases.booking_agent_id== agent_id[0])\
            .join(customer, customer.email == purchases.customer_email)\
            .join(ticket, ticket.ticket_id == purchases.ticket_id)\
            .join(flight, flight.flight_num == ticket.flight_num)\
            .outerjoin(airport1, airport1.airport_name == flight.departure_airport)\
            .join(airport2, airport2.airport_name == flight.arrival_airport)\
            .filter(flight.departure_time >= today_date).all()

    commission_query = flight.query.with_entities(func.sum(flight.price))\
                         .join(ticket, ticket.flight_num == flight.flight_num)\
                         .join(purchases, purchases.ticket_id == ticket.ticket_id)\
                         .filter(purchases.booking_agent_id == agent_id[0]).all()
    commission = .1*float(commission_query[0][0])

    ticket_query = flight.query.with_entities(func.count(flight.flight_num))\
                         .join(ticket, ticket.flight_num == flight.flight_num)\
                         .join(purchases, purchases.ticket_id == ticket.ticket_id)\
                         .filter(purchases.booking_agent_id == agent_id[0]).all()

    num_of_tickets = int(ticket_query[0][0])
    ave_commission = commission/num_of_tickets

    top5byticket = db.session.query(purchases.customer_email, func.count(purchases.customer_email))\
                             .filter(purchases.booking_agent_id == agent_id[0])\
                             .group_by(purchases.customer_email).limit(5).all()

    top5_labels = [row[0] for row in top5byticket]
    top5_values = [row[1] for row in top5byticket]

    top5bycommission = db.session.query(purchases.customer_email, func.sum(flight.price))\
                                 .join(ticket, ticket.ticket_id == purchases.ticket_id)\
                                 .join(flight, flight.flight_num == ticket.flight_num)\
                                 .filter(purchases.booking_agent_id == agent_id[0])\
                                 .group_by(purchases.customer_email).limit(5).all()
    top5_com = [row[0] for row in top5bycommission]
    top_com = [.1*float(row[1]) for row in top5bycommission]


    return render_template('agentHome.html', name = fname, email = current_user.username, 
                                           all_upcoming_flights = upcoming_flights,
                                           all_commission = commission, 
                                           num_of_tickets_sold=num_of_tickets, 
                                           average=ave_commission, x=top5_labels, y=top5_values, 
                                           x2=top5_com, y2=top_com)

@login_required
@main.route('/views', methods = ["GET"])
def views():
    ## ticket and purchases. customers
    time_limit = date.today() - timedelta(days=365)
    past_month = date.today() - timedelta(days=30)
    airline = db.session.query(airline_staff.airline_name).filter(airline_staff.username==current_user.username).first()
    #airport1 = aliased(airport, name ='origin')
    #airport2 = aliased(airport, name = 'destination')

    top_flyers = db.session.query(customer.name, purchases.customer_email, func.count(purchases.customer_email))\
                           .filter(purchases.purchase_date <= date.today())\
                           .filter(purchases.purchase_date >= time_limit)\
                           .join(ticket, ticket.ticket_id == purchases.ticket_id)\
                           .join(customer, customer.email == purchases.customer_email)\
                           .group_by(customer.name,purchases.customer_email).all()

    topAgentsByticket30 = db.session.query(purchases.booking_agent_id, booking_agent.email, func.count(purchases.booking_agent_id))\
                            .filter(purchases.purchase_date <= date.today())\
                            .filter(purchases.purchase_date >= past_month)\
                            .join(booking_agent, booking_agent.booking_agent_id == purchases.booking_agent_id)\
                            .group_by(purchases.booking_agent_id, booking_agent.email).limit(5).all()

    topAgentsByticketYear = db.session.query(purchases.booking_agent_id, booking_agent.email, func.count(purchases.booking_agent_id))\
                            .filter(purchases.purchase_date <= date.today())\
                            .filter(purchases.purchase_date >= time_limit)\
                            .join(booking_agent, booking_agent.booking_agent_id == purchases.booking_agent_id)\
                            .group_by(purchases.booking_agent_id, booking_agent.email).limit(5).all()

    top5ByCommission = db.session.query(purchases.booking_agent_id, booking_agent.email, func.sum(flight.price))\
                                 .filter(purchases.booking_agent_id.isnot(None))\
                                 .filter(purchases.purchase_date <= date.today())\
                                 .filter(purchases.purchase_date >= time_limit)\
                                 .join(ticket, ticket.ticket_id == purchases.ticket_id)\
                                 .join(flight, flight.flight_num == ticket.flight_num)\
                                 .join(booking_agent, booking_agent.booking_agent_id == purchases.booking_agent_id)\
                                 .group_by(purchases.booking_agent_id, booking_agent.email).limit(5).all()
    #agents = [row[1] for row in top5ByCommission]
    #commission = [.1*float(row[2]) for row in top5ByCommission]
    agents=[]
    for row in top5ByCommission:
        id= row[0]
        email = row[1]
        commission = .1*float(row[2])
        agents.append([id, email, commission])

  
    return render_template('views.html', airline = airline[0], 
                                         frequent_flyers = top_flyers,
                                         top_agents_past_month = topAgentsByticket30,
                                         top_agents_year = topAgentsByticketYear,
                                         top_agents_commission = agents)


@main.route('/flights', methods=["POST", 'GET'])
def flights():
    curr_customer = customer.query.filter_by(email=current_user.username).first()
    agent_id = db.session.query(booking_agent.booking_agent_id).filter(booking_agent.email==current_user.username).first()

    id = shortuuid.ShortUUID().random(length=20)
    airline = request.form.get('airline')
    flight = request.form.get('flight')
    customer_email = request.form.get('customer_email')

    issued_ticket = ticket(ticket_id = id, airline_name = airline, flight_num = flight)
    db.session.add(issued_ticket)

    if curr_customer:
        purchase = purchases(ticket_id = id, customer_email = current_user.username, purchase_date = date.today())
    else:
        purchase = purchases(ticket_id = id, customer_email = customer_email, booking_agent_id = agent_id[0], purchase_date = date.today())
   
    db.session.add(purchase)
    db.session.commit()
    return render_template('flights.html',)

