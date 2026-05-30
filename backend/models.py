import datetime
from sqlalchemy import Column, Integer, String, Numeric, Text, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class DestinationSetting(Base):
    __tablename__ = 'destination_settings'
    
    id = Column(Integer, primary_key=True, index=True)
    destination = Column(String(100), unique=True, nullable=False, index=True)
    pickups = Column(JSONB, default=[])       # Array of pickup locations
    stay_places = Column(JSONB, default=[])   # Array of stay locations
    vehicles = Column(JSONB, default=[])      # Array of permitted vehicles
    hotel_categories = Column(JSONB, default=[]) # e.g. ["Deluxe", "Premium", "Luxury"]
    daily_routes = Column(JSONB, default=[])  # Presets for routing
    short_itineraries = Column(JSONB, default=[])
    profit_config = Column(JSONB, default={}) # Flat or tiered percentages
    seasonal_surcharges = Column(JSONB, default=[]) # Date ranges and percentages
    
    # Default Rich Text Editor (RTE) blocks
    inclusions = Column(Text, default="")
    exclusions = Column(Text, default="")
    payment_terms = Column(Text, default="")
    important_note = Column(Text, default="")
    why_choose_us = Column(Text, default="")
    essential_guidelines = Column(Text, default="")
    
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class HotelRate(Base):
    __tablename__ = 'hotel_rates'

    id = Column(Integer, primary_key=True, index=True)
    destination = Column(String(100), nullable=False, index=True)
    stay_place = Column(String(100), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    hotel_name = Column(String(150), nullable=False, index=True)
    website_url = Column(Text, nullable=True)
    
    # Dynamic JSONB pricing arrays: [{"room_type": "Deluxe", "room_price": 4500, "extra_bed_price": 1200, "child_price": 800}]
    room_types = Column(JSONB, nullable=False, default=[])
    
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class TransportRate(Base):
    __tablename__ = 'transport_rates'

    id = Column(Integer, primary_key=True, index=True)
    destination = Column(String(100), nullable=False, index=True)
    pickup_location = Column(String(100), nullable=False)
    vehicle_type = Column(String(100), nullable=False)
    capacity = Column(Integer, nullable=False)
    price_per_day = Column(Numeric(10, 2), nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class Quote(Base):
    __tablename__ = 'quotes'

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(8), unique=True, nullable=False, index=True) # Unique 8-char permalink
    title = Column(String(255), nullable=False) # Generated: Client Name + Destination + slug
    client_name = Column(String(100), nullable=False, index=True)
    client_phone = Column(String(20), nullable=False, index=True)
    client_email = Column(String(100), nullable=True, index=True)
    destination = Column(String(100), nullable=False, index=True)
    booking_status = Column(String(30), default="Pending", index=True) # Pending, Confirmed, Cancelled
    is_starred = Column(Boolean, default=False, index=True)
    follow_up_date = Column(DateTime(timezone=True), nullable=True)
    trip_date = Column(DateTime(timezone=True), nullable=True, index=True)
    pax_count = Column(Integer, default=1, index=True)
    post_quote_discount = Column(Numeric(10, 2), default=0.00)
    
    # Flexible master object container for calculating engine elements
    quote_data = Column(JSONB, nullable=False) 
    
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    payments = relationship("PaymentHistory", back_populates="quote", cascade="all, delete-orphan")
    expenses = relationship("BookingExpense", back_populates="quote", cascade="all, delete-orphan")


class PaymentHistory(Base):
    __tablename__ = 'payment_histories'

    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(Integer, ForeignKey('quotes.id', ondelete="CASCADE"), nullable=False)
    payment_type = Column(String(50), nullable=False) # UPI, Bank Transfer, Cash, Card, Direct to Vendor, Refund
    amount = Column(Numeric(10, 2), nullable=False)
    gateway_fee = Column(Numeric(10, 2), default=0.00)
    net_in_bank = Column(Numeric(10, 2), nullable=False) # amount - gateway_fee (or 0 for direct to vendor/refunds)
    transaction_date = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    remarks = Column(Text, nullable=True)
    
    quote = relationship("Quote", back_populates="payments")


class BookingExpense(Base):
    __tablename__ = 'booking_expenses'

    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(Integer, ForeignKey('quotes.id', ondelete="CASCADE"), nullable=False)
    base_cost_override = Column(Numeric(10, 2), nullable=True)
    vendor_name = Column(String(150), nullable=True)
    amount_paid = Column(Numeric(10, 2), default=0.00)
    expense_date = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    notes = Column(Text, nullable=True)
    
    quote = relationship("Quote", back_populates="expenses")


class GeneralExpense(Base):
    __tablename__ = 'general_expenses'

    id = Column(Integer, primary_key=True, index=True)
    expense_date = Column(DateTime(timezone=True), default=datetime.datetime.utcnow, index=True)
    category = Column(String(100), nullable=False, index=True) # Autocomplete support
    description = Column(Text, nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)
    paid_by_partner = Column(String(100), nullable=False, index=True) # Mapped to partner ledger for reimbursement
    is_recurring = Column(Boolean, default=False)


class RecurringExpenseSetup(Base):
    __tablename__ = 'recurring_expense_setups'

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)
    paid_by_partner = Column(String(100), nullable=False)
    frequency = Column(String(20), nullable=False) # daily, monthly
    last_logged_date = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)


class Partner(Base):
    __tablename__ = 'partners'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    capital_investment = Column(Numeric(12, 2), default=0.00)
    
    # Historical share logs stored dynamically: [{"effective_date": "2026-01-01", "percentage": 35.0}]
    share_history = Column(JSONB, nullable=False, default=[])


class FixedTour(Base):
    __tablename__ = 'fixed_tours'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    destination = Column(String(100), nullable=False, index=True)
    days = Column(Integer, nullable=False)
    master_capacity = Column(Integer, nullable=False)
    
    # Stores structural details, hotel routing matrix, Quill descriptions, and image locations
    itinerary_data = Column(JSONB, nullable=False)
    
    # Specific scheduled dates: [{"start_date": "2026-06-15", "end_date": "2026-06-22", "capacity": 20, "booked_seats": 2, "prices": {...}}]
    departure_dates = Column(JSONB, nullable=False, default=[])
    
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)


class QuickNote(Base):
    __tablename__ = 'quick_notes'

    id = Column(Integer, primary_key=True, index=True)
    group_name = Column(String(100), nullable=False, index=True) # Autocomplete support
    note_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class SystemConfig(Base):
    __tablename__ = 'system_config'
    
    id = Column(Integer, primary_key=True, index=True)
    api_key_hash = Column(String(128), nullable=True) # Timing-safe hash validation
    last_seen_child_url = Column(Text, nullable=True)
    last_seen_timestamp = Column(DateTime(timezone=True), nullable=True)
    
    # Global Parameters
    global_gst_percent = Column(Numeric(5, 2), default=5.00)
    global_pt_percent = Column(Numeric(5, 2), default=0.00)
    global_pg_percent = Column(Numeric(5, 2), default=2.00)
    company_banner_url = Column(Text, nullable=True)
    head_office_address = Column(Text, nullable=True)
