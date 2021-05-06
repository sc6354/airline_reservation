from flask import Blueprint, render_template, session, request, flash, redirect, url_for, make_response
from flask_login import login_required, current_user
from . import db 
from .models import *
from sqlalchemy.orm import aliased
from sqlalchemy import extract,func, or_, desc, distinct, asc
from datetime import datetime, date, timedelta   
import uuid
import shortuuid
from .forms import *

main = Blueprint('main', __name__)

today_date = date.today()
past_month = date.today() - timedelta(days=30)
past6months = date.today() - timedelta(days=180)
past_year = date.today() - timedelta(days=365)
airport1 = aliased(airport, name ='origin')
airport2 = aliased(airport, name = 'destination')     


########## Search Flights Page ########## 
@main.route('/', methods=["POST", 'GET'])
def index():
    if request.method == 'POST':
        origin = request.form.get('departure').upper()
        destination = request.form.get('destination').upper()
        date = request.form.get('date')
        all_flights = db.session.query(flight, airport1, airport2, airplane)\
                                .join(airport1, airport1.airport_name == flight.departure_airport)\
                                .join(airport2, airport2.airport_name == flight.arrival_airport)\
                                .join(airplane, airplane.airplane_id == flight.airplane_id)\
                                .filter(func.date(flight.departure_time) == date)\
                                .filter(or_(airport1.airport_city == origin, airport1.airport_name == origin))\
                                .filter(or_(airport2.airport_city == destination, airport2.airport_name == destination))\
                                .all()

        if current_user.is_anonymous:
            if not all_flights:
                flash('Sorry, no flights found. Change your selection and try again.')
                return (redirect(url_for('main.index')))
            else:
                return render_template('flights.html', flights = all_flights)
        else:
            agent_id = db.session.query(booking_agent.booking_agent_id).filter(booking_agent.email==current_user.username).first()
            if not all_flights:
                flash('Sorry, no flights found. Change your selection and try again.')
                return (redirect(url_for('main.index', agent = agent_id)))
            else:
                return render_template('flights.html', flights = all_flights, agent=agent_id)
        
    return render_template('index.html')


########## Customer Home Page ########## 
@main.route('/profile', methods=["POST", "GET"])
@login_required
def profile():
    today_date = date.today()
    email = "%{0}%".format(current_user.username)
    fname = db.session.query(customer).filter(customer.email.like(email)).first()

    # query upcoming flights
    upcoming_flights = db.session.query(purchases, flight, ticket, airport1, airport2)\
            .filter(purchases.customer_email.like(email))\
            .join(ticket, ticket.ticket_id == purchases.ticket_id)\
            .join(flight, flight.flight_num == ticket.flight_num)\
            .outerjoin(airport1, airport1.airport_name == flight.departure_airport)\
            .join(airport2, airport2.airport_name == flight.arrival_airport)\
            .filter(func.date(flight.departure_time) >= today_date)\
            .order_by(asc(flight.departure_time)).all()

    # query past flights
    past_flights = db.session.query(purchases, flight, ticket, airport1, airport2)\
            .filter(purchases.customer_email.like(email))\
            .join(ticket, ticket.ticket_id == purchases.ticket_id)\
            .join(flight, flight.flight_num == ticket.flight_num)\
            .outerjoin(airport1, airport1.airport_name == flight.departure_airport)\
            .join(airport2, airport2.airport_name == flight.arrival_airport)\
            .filter(func.date(flight.departure_time) <= today_date)\
            .order_by(desc(flight.departure_time)).all()

    # query total spending in past year 
    spending = flight.query.with_entities(func.sum(flight.price))\
                         .join(ticket, ticket.flight_num == flight.flight_num)\
                         .join(purchases, purchases.ticket_id == ticket.ticket_id)\
                         .filter(purchases.customer_email.like(email))\
                         .filter(func.date(flight.departure_time)<= past_year).all()
    
    # query monthly spending 
    spending1 = db.session.query(func.month(purchases.purchase_date), func.sum(flight.price).label('monthly_total'))\
                          .join(ticket, ticket.ticket_id == purchases.ticket_id)\
                          .join(flight, flight.flight_num == ticket.flight_num)\
                          .filter(purchases.customer_email.like(email))\
                          .group_by(func.month(purchases.purchase_date)).all()

    labels = [row[0] for row in spending1]
    values = [float(row[1]) for row in spending1]
    
    if not upcoming_flights:
        flash('Looks like you have no planned trips.')
    
    if request.method =='POST':
        start = request.form.get('start')
        end = request.form.get('end')

        #selective spending history 
        spending2 = db.session.query(func.month(purchases.purchase_date), func.sum(flight.price).label('monthly_total'))\
                          .join(ticket, ticket.ticket_id == purchases.ticket_id)\
                          .join(flight, flight.flight_num == ticket.flight_num)\
                          .filter(purchases.customer_email.like(email))\
                          .filter(purchases.purchase_date >= start)\
                          .filter(purchases.purchase_date <= end)\
                          .group_by(func.month(purchases.purchase_date)).all()

        labels2 = [row[0] for row in spending2]
        values2 = [float(row[1]) for row in spending2]

        return render_template('profile.html', name = fname, email = current_user.username, 
                                           all_upcoming_flights = upcoming_flights, 
                                           all_past_flights = past_flights, 
                                           all_spending = spending[0][0], x =labels, y =values,
                                           x2=labels2, y2=values2, date=start, end_date=end)

    
    return render_template('profile.html', name = fname, email = current_user.username, 
                                           all_upcoming_flights = upcoming_flights, 
                                           all_past_flights = past_flights, 
                                           all_spending = spending[0][0], x =labels, y =values)
    

########## Airline Staff Home Page ########## 
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
    
    # query upcoming flights
    flightsIn30Days = db.session.query(flight, airport1, airport2)\
                                .join(airport1, airport1.airport_name == flight.departure_airport)\
                                .join(airport2, airport2.airport_name == flight.arrival_airport)\
                                .filter(flight.departure_time >= date.today())\
                                .filter(flight.departure_time <= time_limit)\
                                .filter(flight.airline_name == airline[0])\
                                .order_by(asc(flight.departure_time)).all()


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
        entered_flight = db.session.query(flight)\
                           .filter(flight.flight_num == status_form.flight_num.data)\
                           .filter(flight.airline_name == airline[0]).first()
        if not entered_flight:
            flash('No flight found. Please add flight first.')
            return redirect(url_for('main.staffHome'))
        else: 
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

########## Airline Staff View All Flights Page ########## 
@main.route('/more_flights', methods = ["POST", 'GET'])
@login_required
def moreFlights():
    if request.method =='POST':
        start = request.form.get('start')
        end = request.form.get('end')
        origin = request.form.get('origin').upper()
        destination = request.form.get('destination').upper()
        
        airline = db.session.query(airline_staff.airline_name).filter(airline_staff.username==current_user.username).first()

        flightsInDateRange = db.session.query(flight, airport1, airport2, airplane)\
                                       .join(airport1, airport1.airport_name == flight.departure_airport)\
                                       .join(airport2, airport2.airport_name == flight.arrival_airport)\
                                       .join(airplane, airplane.airplane_id == flight.airplane_id)\
                                       .filter(flight.departure_time >= start)\
                                       .filter(flight.departure_time <= end)\
                                       .filter(or_(airport1.airport_city == origin, airport1.airport_name == origin))\
                                       .filter(or_(airport2.airport_city == destination, airport2.airport_name == destination))\
                                       .filter(flight.airline_name == airline[0]).distinct(flight.flight_num)\
                                       .order_by(asc(flight.departure_time)).all()
                                      
        if not flightsInDateRange:
            flash(airline[0] + ' has no flights for this period and route.')
            return (redirect(url_for('main.moreFlights')))
        else:
            return render_template('moreFlights.html', start=start, end=end, more_flights=flightsInDateRange)

    return render_template('moreFlights.html')

########## Airline Staff View Dynamic Reports Page ########## 
@main.route('/reports', methods=["POST", "GET"])
@login_required
def reports():
    # query revenue breakdown in past month
    #not null means there is an id in the agent coloumn of the purchase table
    indirect_revenue_month = db.session.query(purchases, func.sum(flight.price))\
                                .join(ticket, ticket.ticket_id == purchases.ticket_id)\
                                .join(flight, flight.flight_num == ticket.flight_num)\
                                .filter(purchases.purchase_date >= past_month)\
                                .filter(purchases.booking_agent_id.isnot(None)).all()

    direct_revenue_month = db.session.query(purchases, func.sum(flight.price))\
                                .join(ticket, ticket.ticket_id == purchases.ticket_id)\
                                .join(flight, flight.flight_num == ticket.flight_num)\
                                .filter(purchases.purchase_date >= past_month)\
                                .filter(purchases.booking_agent_id.is_(None)).all()
    
    # query revenue breakdonw in past year 
    indirect_revenue_year = db.session.query(purchases, func.sum(flight.price))\
                                .join(ticket, ticket.ticket_id == purchases.ticket_id)\
                                .join(flight, flight.flight_num == ticket.flight_num)\
                                .filter(purchases.purchase_date >= past_year)\
                                .filter(purchases.booking_agent_id.isnot(None)).all()

    direct_revenue_year = db.session.query(purchases, func.sum(flight.price))\
                                .join(ticket, ticket.ticket_id == purchases.ticket_id)\
                                .join(flight, flight.flight_num == ticket.flight_num)\
                                .filter(purchases.purchase_date >= past_year)\
                                .filter(purchases.booking_agent_id.is_(None)).all()
    month_data = [float(direct_revenue_month[0][1]), float(indirect_revenue_month[0][1])]
    year_data = [float(direct_revenue_year[0][1]), float(indirect_revenue_year[0][1])]
    labels = ['Direct Sale', 'Indirect Sales']

    if request.method =='POST':
        start = request.form.get('start')
        end = request.form.get('end')

        # query monthly ticket sale
        results = db.session.query(func.month(purchases.purchase_date),func.count(purchases.ticket_id))\
                            .filter(purchases.purchase_date >= start)\
                            .filter(purchases.purchase_date <= end)\
                            .group_by(func.month(purchases.purchase_date)).all()
        x = [row[0] for row in results]
        y = [row[1] for row in results]

        return render_template('reports.html', date=start, end_date =end, x= x, y=y,
                               month=month_data, labels=labels, year=year_data)

    return render_template('reports.html', month=month_data, labels=labels, year=year_data)

########## Booking Agent Home Page ########## 
@main.route('/agent_home',methods=["POST", "GET"])
@login_required
def agentHome():
    today_date = date.today()
    past_month = date.today() - timedelta(days=30)
    past6months = date.today() - timedelta(days=180)
    past_year = date.today() - timedelta(days=365)
    email = "%{0}%".format(current_user.username)
    airport1 = aliased(airport, name ='origin')
    airport2 = aliased(airport, name = 'destination')

    fname = db.session.query(booking_agent).filter(booking_agent.email.like(email)).first()
    agent_id = db.session.query(booking_agent.booking_agent_id).filter(booking_agent.email.like(email)).first()

    # query upcoming flights for their airline 
    upcoming_flights = db.session.query(purchases, customer, ticket, flight, airport1, airport2)\
            .filter(purchases.booking_agent_id== agent_id[0])\
            .join(customer, customer.email == purchases.customer_email)\
            .join(ticket, ticket.ticket_id == purchases.ticket_id)\
            .join(flight, flight.flight_num == ticket.flight_num)\
            .outerjoin(airport1, airport1.airport_name == flight.departure_airport)\
            .join(airport2, airport2.airport_name == flight.arrival_airport)\
            .filter(flight.departure_time >= today_date).all()

    # query their past month commission
    commission_query = flight.query.with_entities(func.sum(flight.price).label('total sale'))\
                         .join(ticket, ticket.flight_num == flight.flight_num)\
                         .join(purchases, purchases.ticket_id == ticket.ticket_id)\
                         .filter(purchases.purchase_date >= past_month)\
                         .filter(purchases.booking_agent_id == agent_id[0])\
                         .order_by(desc('total sale')).all()

    commission = .1*float(commission_query[0][0])

    # query their past month ticket sales 
    ticket_query = flight.query.with_entities(func.count(flight.flight_num))\
                         .join(ticket, ticket.flight_num == flight.flight_num)\
                         .join(purchases, purchases.ticket_id == ticket.ticket_id)\
                         .filter(purchases.purchase_date >= past_month)\
                         .filter(purchases.booking_agent_id == agent_id[0]).all()

    num_of_tickets = int(ticket_query[0][0])
    ave_commission = round(commission/num_of_tickets, 2)

    # query their top 5 clients by ticket sales
    top5byticket = db.session.query(purchases.customer_email, func.count(purchases.customer_email))\
                             .filter(purchases.booking_agent_id == agent_id[0])\
                             .filter(purchases.purchase_date >= past6months)\
                             .group_by(purchases.customer_email)\
                             .order_by(func.count(purchases.customer_email)).limit(5).all()

    top5_labels = [row[0] for row in top5byticket]
    top5_values = [row[1] for row in top5byticket]

    # query their top 5 clients by commission in past year 
    top5bycommission = db.session.query(purchases.customer_email, func.sum(flight.price).label('total sales'))\
                                 .join(ticket, ticket.ticket_id == purchases.ticket_id)\
                                 .join(flight, flight.flight_num == ticket.flight_num)\
                                 .filter(purchases.booking_agent_id == agent_id[0])\
                                 .filter(purchases.purchase_date >= past_year)\
                                 .group_by(purchases.customer_email)\
                                 .order_by(desc('total sales')).limit(5).all()

    top5_com = [row[0] for row in top5bycommission]
    top_com = [.1*float(row[1]) for row in top5bycommission]

    # query selective commission days
    if request.method =='POST':
        start = request.form.get('agent_start')
        end = request.form.get('agent_end')

        results = flight.query.with_entities(func.sum(flight.price).label('total sale'))\
                        .join(ticket, ticket.flight_num == flight.flight_num)\
                        .join(purchases, purchases.ticket_id == ticket.ticket_id)\
                        .filter(purchases.purchase_date >= start)\
                        .filter(purchases.purchase_date <= end)\
                        .filter(purchases.booking_agent_id == agent_id[0])\
                        .order_by(desc('total sale')).all()
        
        ticket_results = flight.query.with_entities(func.count(flight.flight_num))\
                                     .join(ticket, ticket.flight_num == flight.flight_num)\
                                     .join(purchases, purchases.ticket_id == ticket.ticket_id)\
                                     .filter(purchases.purchase_date >= start)\
                                     .filter(purchases.purchase_date <= end)\
                                     .filter(purchases.booking_agent_id == agent_id[0]).all()
        if results is not None:
            selected_commission = .1*float(results[0][0])
            t = int(ticket_results[0][0])
            selected_ave_commission = round(selected_commission/t, 2)
        else:
            selected_commission =0
            t = 0
            selected_ave_commission =0
        return render_template('agentHome.html',name = fname, email = current_user.username, 
                                all_upcoming_flights = upcoming_flights,all_commission = commission, 
                                num_of_tickets_sold=num_of_tickets, average=ave_commission,
                                x=top5_labels, y=top5_values, x2=top5_com, y2=top_com,start=start, end=end,
                                selected_com= selected_commission, selected_ave=selected_ave_commission,selected_tic=t)


    return render_template('agentHome.html', name = fname, email = current_user.username, 
                                           all_upcoming_flights = upcoming_flights,
                                           all_commission = commission, 
                                           num_of_tickets_sold=num_of_tickets, 
                                           average=ave_commission, x=top5_labels, y=top5_values, 
                                           x2=top5_com, y2=top_com)

########## Airline Staff Views Page ########## 
@login_required
@main.route('/views', methods = ["GET"])
def views():
    airline = db.session.query(airline_staff.airline_name).filter(airline_staff.username==current_user.username).first()

    # query top flyers in the past year 
    top_flyers = db.session.query(customer.name, purchases.customer_email, func.count(purchases.customer_email))\
                           .filter(purchases.purchase_date <= date.today())\
                           .filter(purchases.purchase_date >= past_year)\
                           .join(ticket, ticket.ticket_id == purchases.ticket_id)\
                           .join(customer, customer.email == purchases.customer_email)\
                           .group_by(customer.name,purchases.customer_email).all()

    # query top Agents by number of ticket sold in past month
    topAgentsByticket30 = db.session.query(purchases.booking_agent_id, booking_agent.email, func.count(purchases.booking_agent_id))\
                            .filter(purchases.purchase_date <= date.today())\
                            .filter(purchases.purchase_date >= past_month)\
                            .join(booking_agent, booking_agent.booking_agent_id == purchases.booking_agent_id)\
                            .group_by(purchases.booking_agent_id, booking_agent.email).limit(5).all()

    # query top Agents by number of ticket sold in past year
    topAgentsByticketYear = db.session.query(purchases.booking_agent_id, booking_agent.email, func.count(purchases.booking_agent_id))\
                            .filter(purchases.purchase_date <= date.today())\
                            .filter(purchases.purchase_date >= past_year)\
                            .join(booking_agent, booking_agent.booking_agent_id == purchases.booking_agent_id)\
                            .group_by(purchases.booking_agent_id, booking_agent.email).limit(5).all()
    
    # query top Agents by commission in past year 
    top5ByCommission = db.session.query(purchases.booking_agent_id, booking_agent.email, func.sum(flight.price))\
                                 .filter(purchases.booking_agent_id.isnot(None))\
                                 .filter(purchases.purchase_date <= date.today())\
                                 .filter(purchases.purchase_date >= past_year)\
                                 .join(ticket, ticket.ticket_id == purchases.ticket_id)\
                                 .join(flight, flight.flight_num == ticket.flight_num)\
                                 .join(booking_agent, booking_agent.booking_agent_id == purchases.booking_agent_id)\
                                 .group_by(purchases.booking_agent_id, booking_agent.email).limit(5).all()
    agents=[]
    for row in top5ByCommission:
        id= row[0]
        email = row[1]
        commission = .1*float(row[2])
        agents.append([id, email, commission])
    
    # query top 3 destinations in past 3 months 
    topDestinations = db.session.query(airport.airport_city, func.count(ticket.flight_num).label('total tickets'))\
                                .join(flight, flight.arrival_airport==airport.airport_name)\
                                .join(ticket, ticket.flight_num == flight.flight_num)\
                                .join(purchases, purchases.ticket_id == ticket.ticket_id)\
                                .filter(purchases.purchase_date <= date.today())\
                                .filter(purchases.purchase_date >= (date.today() - timedelta(days=60)))\
                                .group_by(airport.airport_city).order_by(desc('total tickets')).limit(3).all()

    # query top 3 destinations in past year 
    topDestinationsYear = db.session.query(airport.airport_city, func.count(ticket.flight_num).label('total tickets'))\
                                .join(flight, flight.arrival_airport==airport.airport_name)\
                                .join(ticket, ticket.flight_num == flight.flight_num)\
                                .join(purchases, purchases.ticket_id == ticket.ticket_id)\
                                .filter(purchases.purchase_date <= date.today())\
                                .filter(purchases.purchase_date >= past_year)\
                                .group_by(airport.airport_city).order_by(desc('total tickets')).limit(3).all()

  
    return render_template('views.html', airline = airline[0], 
                                         frequent_flyers = top_flyers,
                                         top_agents_past_month = topAgentsByticket30,
                                         top_agents_year = topAgentsByticketYear,
                                         top_agents_commission = agents,
                                         top_places_in_3_months = topDestinations,
                                         top_places_in_year = topDestinationsYear)

########## Customer and Agent Purchase Flight Page ########## 
@main.route('/flights', methods=["POST", 'GET'])
def flights():
    id = shortuuid.ShortUUID().random(length=11)
    airline = request.form.get('airline')
    flight = request.form.get('flight')
    customer_email = request.form.get('customer_email')

    curr_customer = customer.query.filter_by(email=customer_email).first()
    agent_id = db.session.query(booking_agent.booking_agent_id).filter(booking_agent.email==current_user.username).first()

    issued_ticket = ticket(ticket_id = id, airline_name = airline, flight_num = flight)
    db.session.add(issued_ticket)
    db.session.flush()

    if curr_customer:
        purchase = purchases(purchase_date = date.today())
        purchase.ticket_id = issued_ticket.ticket_id
        purchase.customer_email = curr_customer.email
        #purchase = purchases(ticket_id = id, customer_email = current_user.username, purchase_date = date.today())
    else:
        purchase = purchases(booking_agent_id = agent_id[0], purchase_date = date.today())
        purchase.ticket_id = issued_ticket.ticket_id
        purchase.customer_email = customer_email  
   
    db.session.add(purchase)
    db.session.commit()
    return render_template('index.html', agent=agent_id )

