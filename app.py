from typing import List
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from marshmallow import ValidationError
from sqlalchemy import Column, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import os
from datetime import date
from flask_marshmallow import Marshmallow
import logging
logging.basicConfig(level=logging.DEBUG)


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')


class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class = Base)
ma = Marshmallow()

db.init_app(app)
ma.init_app(app)


#========== Models ==========

service_mechanics = db.Table(
    "service_mechanics",
    Base.metadata,
    Column("ticket_id", db.ForeignKey("service_tickets.id")),
    Column("mechanic_id", db.ForeignKey("mechanics.id"))
)

class Customer(Base):
    __tablename__ = 'customers'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), nullable = False)
    email: Mapped[str] = mapped_column(db.String(200), nullable= False, unique=True)
    phone: Mapped[str] = mapped_column(db.String(25))

    service_tickets: Mapped[List['ServiceTicket']] = db.relationship(back_populates = 'customer')


class ServiceTicket (Base):
    __tablename__ = 'service_tickets'

    id: Mapped[int] = mapped_column(primary_key=True)
    vin: Mapped[str] = mapped_column (db.String(100), nullable=False)
    service_date: Mapped[date] = mapped_column (nullable=False)
    service_desc: Mapped[str] = mapped_column (db.String(300))
    customer_id: Mapped[int] = mapped_column(db.ForeignKey('customers.id'))

    customer: Mapped['Customer'] = db.relationship(back_populates = 'service_tickets')
    mechanics: Mapped[List["Mechanic"]] = db.relationship(secondary = service_mechanics, back_populates='service_tickets')

class Mechanic (Base):
    __tablename__ = 'mechanics'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(100), nullable = False)
    email: Mapped[str] = mapped_column(db.String(200), nullable= False, unique=True)
    phone: Mapped[str] = mapped_column(db.String(25))
    salary: Mapped[float] = mapped_column()

    service_tickets: Mapped[List['ServiceTicket']] = db.relationship(secondary = service_mechanics, back_populates = 'mechanics')

#========== Schemas ==========

class CustomerSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Customer

class ServiceTicketSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ServiceTicket

class MechanicSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Mechanic

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many = True)

service_ticket_schema = ServiceTicketSchema()
service_tickets_schema = ServiceTicketSchema(many = True)

mechanic_schema = MechanicSchema()
mechanics_schema = MechanicSchema(many = True)

#========= Routes ===========

#Create Customer
@app.route("/customers", methods = ['POST'])
def create_customer():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_customer = Customer(name=customer_data['name'], email=customer_data['email'], phone=customer_data['phone'])
    db.session.add(new_customer)
    db.session.commit()

    return customer_schema.jsonify(new_customer), 201

#Retrieve Customers
@app.route("/customers", methods=["GET"])
def get_customers():
    query = select(Customer)
    customers = db.session.execute(query).scalars().all()

    return customers_schema.jsonify(customers), 200

#Retrieve Customer
@app.route("/customers/<int:customer_id>", methods=["GET"])
def get_customer(customer_id):
    customer = db.session.get(Customer, customer_id)

    return customer_schema.jsonify(customer), 200

#Update Customer
@app.route("/customers/<int:customer_id>", methods=['PUT'])
def update_customer(customer_id):
    customer = db.session.get(Customer, customer_id)

    if customer == None:
        return jsonify({"Message": "Invalid id"}), 400
    
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    for field, value in customer_data.items():
        if value:
            setattr(customer, field, value)
    
    db.session.commit()
    return customer_schema.jsonify(customer), 200

#Delete Customer
@app.route("/customers/<int:customer_id>", methods=['DELETE'])
def delete_customer(customer_id):
    customer = db.session.get(Customer, customer_id)

    if customer == None:
        return jsonify({"Message": "Invalid id"}), 400
    
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"Message": f"Successfully deleted customer {customer_id}!"})


if __name__ == '__main__':
    
    with app.app_context():
        db.create_all()

    app.run()