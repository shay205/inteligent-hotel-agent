"""Builds every manager once and bundles them, so the UI only needs one object."""
from dataclasses import dataclass

from hotel_agent.ai.nlp.chatbot import HotelChatbot
from hotel_agent.ai.recommender import RoomRecommender
from hotel_agent.ai.service_recommender import ServiceRecommender
from hotel_agent.config import DB_PATH
from hotel_agent.database.connection import Database
from hotel_agent.database.seed_data import seed_demo_data
from hotel_agent.reporting.reports import ReportGenerator
from hotel_agent.services.booking_manager import BookingManager
from hotel_agent.services.conversation_manager import ConversationManager
from hotel_agent.services.customer_manager import CustomerManager
from hotel_agent.services.room_manager import RoomManager
from hotel_agent.services.service_manager import ServiceManager


@dataclass
class AppContext:
    db: Database
    rooms: RoomManager
    customers: CustomerManager
    bookings: BookingManager
    services: ServiceManager
    conversations: ConversationManager
    recommender: RoomRecommender
    service_recommender: ServiceRecommender
    chatbot: HotelChatbot
    reports: ReportGenerator


def build_context(db_path=DB_PATH, seed: bool = True) -> AppContext:
    db = Database(db_path)
    if seed:
        seed_demo_data(db)
    rooms = RoomManager(db)
    customers = CustomerManager(db)
    bookings = BookingManager(db, rooms, customers)
    services = ServiceManager(db)
    recommender = RoomRecommender(rooms, bookings)
    service_recommender = ServiceRecommender(services)
    chatbot = HotelChatbot(rooms, bookings, services, recommender, service_recommender)
    return AppContext(db, rooms, customers, bookings, services, ConversationManager(db),
                      recommender, service_recommender, chatbot, ReportGenerator(db))