from datetime import datetime
from uuid import uuid4
import random
#API
#1.show_reservation
#2.pay_by_credit_card
#3.pay_by_qr
#4.get_flight_instance_matches
#5.select_flight //return flight_instance + show flight seats
#6.get_all_services //return services_list
#7.check_in //return boarding pass
#8.create_flight
#9.create_flight_instance



class AirportSystem:                                     
    def __init__(self):
        self.__airport_list = []
        self.__aircraft_list = []
        self.__flight_list = []
        self.__flight_instance_list = []
        self.__service_list = []
        self.__reservation_list = []

    @property
    def airport_list(self):
        return self.__airport_list

    @property
    def aircraft_list(self):
        return self.__aircraft_list
        
    @property
    def flight_list(self):
        return self.__flight_list
    
    @property
    def flight_instance_list(self):
        return self.__flight_instance_list
    
    @property
    def service_list(self):
        return self.__service_list

    @service_list.setter
    def service_list(self, service):
        self.__service_list.append(service)
    
    def get_flight_instance_matches(self, starting_location, destination, depart_date, return_date = None):
        departing_flight_instance = []
        returning_flight_instance = []

        for flight_instance in self.__flight_instance_list:
            if flight_instance.starting_location.name == starting_location and flight_instance.destination.name == destination and flight_instance.date == depart_date:
                flight_instance_info = flight_instance.get_flight_instance_info_for_showing()
                
                departing_flight_instance.append(flight_instance_info)

        if return_date != None:
            for flight_instance in self.__flight_instance_list:
                if flight_instance.destination.name == starting_location and flight_instance.starting_location.name == destination and flight_instance.date == return_date:
                    flight_instance_info = flight_instance.get_flight_instance_info_for_showing()

                    returning_flight_instance.append(flight_instance_info)

        return (departing_flight_instance, returning_flight_instance)

    def get_flight_instance(self, flight_number, date):
        for flight_instance in self.__flight_instance_list:
            if flight_instance.flight_number == flight_number and flight_instance.date == date:
                return flight_instance  
        
    def pay_by_qr(self, flight_instance_list, passenger_list, flight_seats_list):
        reservation = self.create_reservation_for_paid(flight_instance_list, passenger_list, flight_seats_list, True)
        if reservation:
            payment_method = Qr()
            reservation.create_transaction(payment_method)
            reservation.generate_booking_reference()
            reservation.calculate_total_cost()
            self.__reservation_list.append(reservation)
            return reservation.get_reservation_info_for_showing()
        return "Could not reserve flight. Please try again."

    def pay_by_credit_card(self, card_number, cardholder_name, expiry_date, cvv, flight_instance_list, passenger_list, flight_seats_list):
        reservation = self.create_reservation_for_paid(flight_instance_list, passenger_list, flight_seats_list, True)
        if reservation:
            payment_method = CreditCard(card_number, cardholder_name, expiry_date, cvv)
            reservation.create_transaction(payment_method)
            reservation.generate_booking_reference()
            reservation.calculate_total_cost()
            self.__reservation_list.append(reservation)
            return reservation.get_reservation_info_for_showing()
        return "Could not reserve flight. Please try again."

    def get_service(self, service_name):
        for service in self.__service_list:
            if service.service_name == service_name:
                return service
        return None
    
    def show_unpaid_reservation_cost(self, flight_instance_list, passenger_list, flight_seats_list):
        reservation = self.create_reservation_for_paid(flight_instance_list, passenger_list, flight_seats_list, False)
        if isinstance(reservation, str):
            return "Normal Seat Full for People not select"
        if reservation:
            reservation_cost = reservation.calculate_total_cost()
            return reservation_cost
        return "Could not calculate cost. Please try again."
    
    def create_reservation_for_paid(self, flight_instance_list, passenger_list, flight_seats_list, mark_seats_as_occupied=False):
        reservation = Reservation()
        
        #0 = title, 1 = first_name, 2 = middle_name, 3 = last_name, 4 = birthday, 5 = phone_number, 6 = email, 7 = service_list
        for passenger_data_dict in passenger_list:
            title = passenger_data_dict.get("title")
            first_name = passenger_data_dict.get("first_name")
            last_name = passenger_data_dict.get("last_name")
            birthday = passenger_data_dict.get("birthday")
            phone_number = passenger_data_dict.get("phone_number")
            email = passenger_data_dict.get("email")
            middle_name = passenger_data_dict.get("middle_name")
            
            reservation.add_passenger(title, first_name, last_name, birthday, phone_number, email, middle_name)
            passenger = reservation.get_passenger_by_name(first_name, last_name, middle_name)
            service_list = passenger_data_dict.get("service_list")
            for service_data in service_list:
                #0 = service_name, 1 = price_per_unit
                service = self.get_service(service_data)
                passenger.add_service(service)
        
        #0 = flight_number, 1 = date
        for flight_instance_data in flight_instance_list:
            flight_instance = self.get_flight_instance(flight_instance_data.get("flight_number"), flight_instance_data.get("date"))
            reservation.add_flight_instance(flight_instance)
        
        #flight_seat_list data structure: [[seat1, seat2], [seat3, seat4]]
        #                                        /\              /\
        #                                     departing       returning
        
        for index,flight_instance in enumerate(reservation.flight_instances_list):
            amount_normal_seat = 0
            for seat_number in flight_seats_list[index]:
                if flight_instance.get_flight_seat(seat_number).seat_category.seat_category_name == "normal_seat":
                    amount_normal_seat += 1
            if flight_instance.amount_of_normal_seats_available < amount_normal_seat + len(passenger_list) - len(flight_seats_list[index]):
                return "Normal seats are all full"
            
        
        new_flight_seat_list = []
        
        for index, flight_instance in enumerate(reservation.flight_instances_list):
            sub_list_of_flight_seats = []
            #check each sub_list of flight_seats
            for flight_seat_number in flight_seats_list[index]:
                flight_seat = flight_instance.get_flight_seat(flight_seat_number)
                
                #if flight_seat not found or is occupied; unoccupy all previous checked flight_seats and abort
                if not flight_seat or flight_seat.occupied:
                    for checked_sub_list in new_flight_seat_list:
                        for checked_flight_seat in checked_sub_list:
                            checked_flight_seat.occupied = False
                    
                    return None
                
                if mark_seats_as_occupied:
                    flight_seat.occupied = True
                    if flight_seat.seat_category.seat_category_name == "normal_seat":
                        flight_instance.decrease_amount_of_normal_seats_available(1)
                    
                sub_list_of_flight_seats.append(flight_seat)
            
            new_flight_seat_list.append(sub_list_of_flight_seats)

        if mark_seats_as_occupied:
            for index,flight_instance in enumerate(reservation.flight_instances_list):
                flight_instance.decrease_amount_of_normal_seats_available(len(passenger_list) - len(flight_seats_list[index]))

        reservation.flight_seat_list = new_flight_seat_list
        return reservation

    def get_reservation(self, booking_reference):
        for reservation in self.__reservation_list:
            if reservation.booking_reference == booking_reference:
                return reservation
        return None
    
    def check_in(self, booking_reference, last_name):
        reservation = self.get_reservation(booking_reference)
        if reservation:
            
            passenger_list = reservation.get_passenger_list_by_last_name(last_name)
            boarding_passes_list = []
            
            for flight_instance in reservation.flight_instances_list:
                reservation.add_random_flight_seat(flight_instance)
                
            for passenger in passenger_list:
                boarding_passes_list.extend(reservation.create_boarding_pass(passenger))
                 
            return boarding_passes_list
    
class Reservation:
    def __init__(self):
        self.__booking_reference = None
        self.__flight_instance_list = []
        self.__passenger_list = []
        self.__flight_seat_list = []
        self.__total_cost = 0                                                                                                   
        self.__transaction = None
        self.__boarding_passes_list = []
        
    @property
    def flight_instances_list(self):
        return self.__flight_instance_list

    @property
    def flight_seat_list(self):
        return self.__flight_seat_list
    
    @flight_seat_list.setter
    def flight_seat_list(self, flight_seat_list):
        self.__flight_seat_list = flight_seat_list
    
    @property
    def transaction(self):
        return self.__transaction
    
    @transaction.setter
    def transaction(self, transaction):
        self.__transaction = transaction

    @property
    def booking_reference(self):
        return self.__booking_reference

    @property
    def boarding_passes_list(self):
        return self.__boarding_passes_list
    
    def add_passenger(self, title, first_name, last_name, birthday, phone_number, email, middle_name):
        passenger = Passenger(title, first_name, last_name, birthday, phone_number, email, middle_name)
        self.__passenger_list.append(passenger)
    
    def add_flight_seat(self, flight_seat):
        self.__flight_seat_list.append(flight_seat)
        
    def add_flight_instance(self, flight_instance):
        self.__flight_instance_list.append(flight_instance)
    
    def get_passenger_by_name(self, first_name, last_name, middle_name = None):
        for passenger in self.__passenger_list:
            if passenger.first_name == first_name and passenger.middle_name == middle_name and passenger.last_name == last_name:
                return passenger
            elif passenger.first_name == first_name and passenger.last_name == last_name:
                return passenger
        return None
    
    def generate_booking_reference(self):
        split_uuid = str(uuid4()).split("-")
        short_uuid = split_uuid[0] + split_uuid[1]
        self.__booking_reference = short_uuid
    
    def get_passenger_list_by_last_name(self, last_name):
        matched_passenger_list = []
        for passenger in self.__passenger_list:
            if passenger.last_name == last_name:
                matched_passenger_list.append(passenger)
        return matched_passenger_list
    
    def create_transaction(self, payment_method):
        if payment_method:
            transaction = Transaction(payment_method)
            self.__transaction = transaction
    
    def calculate_total_cost(self):
        flight_instances_cost = 0
        flight_seats_cost = 0
        services_cost = 0
        
        for flight_instance in self.__flight_instance_list:
            flight_instances_cost += flight_instance.cost * len(self.__passenger_list)
        
        for flight_seat_sub_list in self.__flight_seat_list:
            for flight_seat in flight_seat_sub_list:
                flight_seats_cost += flight_seat.seat_category.seat_price
                
        for passenger in self.__passenger_list:
            for service in passenger.service_list:
                services_cost += service.total_cost

        self.__total_cost = flight_instances_cost + flight_seats_cost + services_cost
        return {"flight_instances_cost": flight_instances_cost,
                "flight_seats_cost": flight_seats_cost,
                "services_cost": services_cost,
                "total_cost": self.__total_cost}
    
    def add_random_flight_seat(self, flight_instance):
        flight_instance_index = self.__flight_instance_list.index(flight_instance)
        chosen_seat_amount = len(self.__flight_seat_list[flight_instance_index])
        passenger_amount = len(self.__passenger_list)
        for amount in range(chosen_seat_amount, passenger_amount):
            while(True):
                random_seat = random.choice(flight_instance.flight_seat_list)
                if random_seat.occupied == False and random_seat.seat_category.seat_category_name == "normal_seat":
                    random_seat.occupied = True
                    self.__flight_seat_list[flight_instance_index].append(random_seat)
                    break
        return "success"
    
    def get_reservation_info_for_showing(self):
        reservation_info = {}
        reservation_info["booking_reference"] = self.__booking_reference
        reservation_info["flight_instance_list"] = {}

        reservation_info["transaction"] = self.__transaction
        
        for index, flight_instance in enumerate(self.__flight_instance_list):
            flight_instance_info = flight_instance.get_flight_instance_info_for_showing()
            location_text = "departing_flight" if index == 0 else "returning_flight"
            flight_instance_info["date"] = flight_instance.date
            flight_instance_info["from"] = flight_instance.starting_location.name
            flight_instance_info["to"] = flight_instance.destination.name
            flight_instance_info.pop("cost")
            reservation_info["flight_instance_list"][location_text] = flight_instance_info
        
        for index, flight_seat_list in enumerate(self.__flight_seat_list):
            flight_seat_info = []
            for flight_seat in flight_seat_list:
                flight_seat_info.append(flight_seat.seat_number)
            location_text = "departing_flight" if index == 0 else "returning_flight"
            reservation_info["flight_instance_list"][location_text]["flight_seat_list"] = flight_seat_info
        
        reservation_info["passenger_list"] = self.__passenger_list
        return reservation_info
    
    def create_boarding_pass(self, passenger):
        passenger_index = self.__passenger_list.index(passenger)
        boarding_pass_list = []
        for index, flight_instance in enumerate(self.__flight_instance_list):
            flight_number = flight_instance.flight_number
            flight_seat_number = self.__flight_seat_list[index][passenger_index].seat_number
            depart_date = flight_instance.date
            boarding_pass = BoardingPass(flight_number, flight_seat_number, self.__booking_reference, depart_date, passenger)
            boarding_pass_list.append(boarding_pass)
        return boarding_pass_list
    
class User:
    def __init__(self, title, first_name, last_name, birthday, phone_number, email , middle_name):
        self.__title = title
        self.__first_name = first_name
        self.__middle_name = middle_name
        self.__last_name = last_name
        self.__birthday = birthday
        self.__phone_number = phone_number
        self.__email = email
        
    @property
    def title(self):
        return self.__title
    
    @property
    def first_name(self):
        return self.__first_name
    
    @property
    def middle_name(self):
        return self.__middle_name
    
    @property
    def last_name(self):
        return self.__last_name

class Passenger(User):
    def __init__(self, title, first_name, last_name, birthday, phone_number , email , middle_name):
        super().__init__(title, first_name, last_name, birthday, phone_number , email, middle_name)
        self.__service_list = []

    @property
    def service_list(self):
        return self.__service_list
    
    def add_service(self, service):
        self.__service_list.append(service)
class Admin(User):
    pass

class BoardingPass:
    def __init__(self, flight_number, flight_seat_number, booking_reference, depart_date, passenger):
        flight_instance = nokair.get_flight_instance(flight_number, depart_date)
        self.__flight_seat_number = flight_seat_number
        self.__flight_number = flight_number
        if passenger.middle_name:
            self.__passenger_name = f"{passenger.title} {passenger.first_name} {passenger.middle_name} {passenger.last_name}"
        else:
            self.__passenger_name = f"{passenger.title} {passenger.first_name} {passenger.last_name}"
        self.__aircraft_number = flight_instance.aircraft.aircraft_number
        self.__booking_reference = booking_reference
        self.__departure_date = depart_date
        self.__starting_location = flight_instance.starting_location.name
        self.__destination = flight_instance.destination.name

class Flight:
    def __init__(self, starting_location, destination):
        self.__starting_location = starting_location
        self.__destination = destination

    @property
    def starting_location(self):
        return self.__starting_location
    
    @property
    def destination(self):
        return self.__destination

class FlightInstance(Flight):
    def __init__(self, flight, flight_number, departure_time, arrival_time, aircraft, date, cost):
        super().__init__(flight.starting_location, flight.destination)
        self.__flight_seat_list = []
        for seat in aircraft.seat_list:
            self.__flight_seat_list.append(FlightSeat(seat))
        self.__flight_number = flight_number
        self.__departure_time = departure_time
        self.__arrival_time = arrival_time
        self.__aircraft = aircraft
        self.__date = date
        self.__cost = int(cost)
        self.__amount_of_normal_seats_available = self.get_amount_of_normal_seats()
    
    @property
    def flight_number(self):
        return self.__flight_number
    
    @property
    def departure_time(self):
        return self.__departure_time
    
    @property
    def arrival_time(self):
        return self.__arrival_time
    
    @property
    def aircraft(self):
        return self.__aircraft
    
    @property
    def date(self):
        return self.__date
    
    @property
    def cost(self):
        return self.__cost

    @property
    def flight_seat_list(self):
        return self.__flight_seat_list
    
    @property
    def amount_of_normal_seats_available(self):
        return self.__amount_of_normal_seats_available

    def get_flight_seat(self, seat_number):
        for flight_seat in self.__flight_seat_list:
            if flight_seat.seat_number == seat_number:
                return flight_seat
    
    def get_flight_instance_info_for_showing(self):
        return {"departure_time": self.departure_time,
                "arrival_time": self.arrival_time,
                "flight_number": self.flight_number,
                "aircraft_number": self.aircraft.aircraft_number,
                "cost": self.cost}
    
    def get_amount_of_normal_seats(self):
        amount = 0
        for flight_seat in self.__flight_seat_list:
            if flight_seat.seat_category.seat_category_name == "normal_seat":
                amount += 1
        return amount
    
    def decrease_amount_of_normal_seats_available(self, amount):
        self.__amount_of_normal_seats_available -= amount
    
class Aircraft:
    def __init__(self, aircraft_number):
        self.__seat_list = self.__init_default_seat_list()
        self.__aircraft_number = aircraft_number

    @property
    def aircraft_number(self):
        return self.__aircraft_number
    
    @property
    def seat_list(self):
        return self.__seat_list
    
    def __init_default_seat_list(self):
        seats_data = []
        for r in range(1,6):
            for c in range(0,3):
                alphabets = "ABCDEF"
                seat_id = f"{alphabets[c]}{r}"
                seat_category = SeatCategory("normal_seat", 200)
                if r <= 1:
                    seat_category = SeatCategory("premium_seat", 600)
                elif r <= 2:
                    seat_category = SeatCategory("happy_seat", 400)
                seats_data.append(Seats(seat_id, seat_category))
        return seats_data

class Airport:
    def __init__(self, name, short_name):
            self.__name = name
            self.__short_name = short_name
            
    @property
    def name(self):
            return self.__name

class Seats:
    def __init__(self, seat_number, seat_category):
        self.__seat_number = seat_number
        self.__seat_category = seat_category

    @property
    def seat_number(self):
        return self.__seat_number
    
    @property
    def seat_category(self):
        return self.__seat_category

class FlightSeat(Seats):
    def __init__(self, seat):
        super().__init__(seat.seat_number, seat.seat_category)
        self.__occupied = False
    
    @property
    def occupied(self):
        return self.__occupied
    
    @occupied.setter
    def occupied(self, occupied):
        self.__occupied = occupied
        return "Success"

class SeatCategory:
    def __init__(self, seat_category_name, price_per_unit):
        self.__seat_category_name = seat_category_name
        self.__price = int(price_per_unit)

    @property
    def seat_price(self) :
        return self.__price

    @property
    def seat_category_name(self):
        return self.__seat_category_name

class PaymentMethod:
    def __init__(self):
        self.__payment_fee = 0
        
    @property
    def payment_fee(self):
        return self.__payment_fee


class CreditCard(PaymentMethod):
    def __init__(self, card_number, cardholder_name, expiry_date, cvv):
        self.__card_number = card_number
        self.__cardholder_name = cardholder_name
        self.__expiry_date = expiry_date
        self.__cvv = cvv
        self.__payment_fee = 240
    

class Qr(PaymentMethod):
    pass

class Transaction:
    def __init__(self, payment_method:PaymentMethod):
        self.__paid_time = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        self.__payment_method = payment_method.__class__.__name__

class Service:
    def __init__(self, service_name, price_per_unit):
        self.__service_name = service_name
        self.__price_per_unit = float(price_per_unit)
        self.__total_cost = price_per_unit

    @property
    def price_per_unit(self):
        return self.__price_per_unit

    @property
    def total_cost(self):
        return self.__total_cost
    
    @property
    def service_name(self):
        return self.__service_name

    @total_cost.setter
    def total_cost(self, total_cost):
        self.__total_cost = total_cost
        
    def get_service_info_for_showing(self):
        return {"service_name": self.__service_name, "total_cost": self.__total_cost}

class Insurance(Service):
    def __init__(self, service_name, price_per_unit):
        super().__init__(service_name, price_per_unit)
        self.total_cost = price_per_unit


class Baggage(Service):
    def __init__(self, service_name, price_per_unit, weight):
        super().__init__(service_name, price_per_unit)
        self.__weight = weight
        self.total_cost = price_per_unit * weight

nokair = AirportSystem()
nokair.airport_list.append(Airport("Don Mueang", "DMK"))
nokair.airport_list.append(Airport("Chiang Mai", "CNX"))
nokair.airport_list.append(Airport("Phuket", "HKT"))

nokair.flight_list.append(Flight(nokair.airport_list[0], nokair.airport_list[1])) # 0 : 0 --> 1
nokair.flight_list.append(Flight(nokair.airport_list[1], nokair.airport_list[0])) # 1 : 1 --> 0

nokair.flight_list.append(Flight(nokair.airport_list[0], nokair.airport_list[2])) # 2 : 0 --> 2 
nokair.flight_list.append(Flight(nokair.airport_list[2], nokair.airport_list[0])) # 3 : 2 --> 0

nokair.flight_list.append(Flight(nokair.airport_list[1], nokair.airport_list[2])) # 4 : 1 --> 2
nokair.flight_list.append(Flight(nokair.airport_list[2], nokair.airport_list[1])) # 5 : 2 --> 1

nokair.aircraft_list.append(Aircraft("101"))
nokair.aircraft_list.append(Aircraft("102"))
nokair.aircraft_list.append(Aircraft("103"))

# 0 --> 1 / 1 --> 0
nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[0], "F1", "8:00", "10:00", nokair.aircraft_list[0], "2024-03-13", 1000))
nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[0], "F3", "11:00", "13:00", nokair.aircraft_list[0], "2024-03-13", 2000))
nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[0], "F5", "20:00", "22:00", nokair.aircraft_list[0], "2024-03-13", 800))
nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[0], "F1", "8:00", "10:00", nokair.aircraft_list[0], "2024-03-14", 1300))
nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[0], "F3", "11:00", "13:00", nokair.aircraft_list[0], "2024-03-14", 2100))
nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[0], "F5", "20:00", "22:00", nokair.aircraft_list[0], "2024-03-14", 800))
nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[0], "F1", "8:00", "10:00", nokair.aircraft_list[0], "2024-03-15", 1300))
nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[0], "F3", "11:00", "13:00", nokair.aircraft_list[0], "2024-03-15", 2400))
nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[0], "F5", "20:00", "22:00", nokair.aircraft_list[0], "2024-03-15", 2800))

nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[1], "F2", "10:00", "12:00", nokair.aircraft_list[0], "2024-03-14", 1000))
nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[1], "F4", "14:00", "15:00", nokair.aircraft_list[0], "2024-03-14", 2000))
nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[1], "F6", "20:00", "22:00", nokair.aircraft_list[0], "2024-03-14", 800))
nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[1], "F2", "10:00", "12:00", nokair.aircraft_list[0], "2024-03-15", 1200))
nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[1], "F4", "14:00", "15:00", nokair.aircraft_list[0], "2024-03-15", 2200))
nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[1], "F6", "20:00", "22:00", nokair.aircraft_list[0], "2024-03-15", 1000))

# 0 --> 2 / 2 --> 0
#  something error 
nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[2], "G1", "8:00", "10:00", nokair.aircraft_list[1], "2024-03-13", 1200))
nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[2], "G3", "11:00", "13:00", nokair.aircraft_list[1], "2024-03-13", 2600))
nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[2], "G5", "20:00", "22:00", nokair.aircraft_list[1], "2024-03-13", 1560))
nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[2], "G1", "8:00", "10:00", nokair.aircraft_list[1], "2024-03-14", 1100))
nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[2], "G3", "11:00", "13:00", nokair.aircraft_list[1], "2024-03-14", 2800))
nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[2], "G5", "20:00", "22:00", nokair.aircraft_list[1], "2024-03-14", 1600))
nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[2], "G1", "8:00", "10:00", nokair.aircraft_list[1], "2024-03-15", 1700))
nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[2], "G3", "11:00", "13:00", nokair.aircraft_list[1], "2024-03-15", 2350))
nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[2], "G5", "20:00", "22:00", nokair.aircraft_list[1], "2024-03-15", 1970))

nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[3], "G2", "10:00", "12:00", nokair.aircraft_list[1], "2024-03-14", 1510))
nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[3], "G4", "14:00", "15:00", nokair.aircraft_list[1], "2024-03-14", 2100))
nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[3], "G6", "20:00", "22:00", nokair.aircraft_list[1], "2024-03-14", 3000))
nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[3], "G2", "10:00", "12:00", nokair.aircraft_list[1], "2024-03-15", 1390))
nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[3], "G4", "14:00", "15:00", nokair.aircraft_list[1], "2024-03-15", 2760))
nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[3], "G6", "20:00", "22:00", nokair.aircraft_list[1], "2024-03-15", 3210))

nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[4], "H1", "8:00", "10:00", nokair.aircraft_list[2], "2024-03-13", 1200))
nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[4], "H3", "11:00", "13:00", nokair.aircraft_list[2], "2024-03-13", 2300))
nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[4], "H5", "20:00", "22:00", nokair.aircraft_list[2], "2024-03-13", 1900))

nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[5], "H2", "10:00", "12:00", nokair.aircraft_list[2], "2024-03-14", 1310))
nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[5], "H4", "14:00", "15:00", nokair.aircraft_list[2], "2024-03-14", 2500))
nokair.flight_instance_list.append(FlightInstance(nokair.flight_list[5], "H6", "20:00", "22:00", nokair.aircraft_list[2], "2024-03-14", 3200))

nokair.service_list = Insurance("Insurance", 100)
nokair.service_list = Baggage("+5kg Baggage", 100, 5)
nokair.service_list = Baggage("+10kg Baggage", 100, 10)
nokair.service_list = Baggage("+15kg Baggage", 100, 15)