from sqlalchemy import (JSON, TIMESTAMP, Boolean, Column, ForeignKey, Integer,
                        String, Table, DateTime, func, DECIMAL)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from fastapi import Depends
from ..services.async_database import get_async_session
from app.services.async_database import Base
import datetime

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    order_number = Column(Integer, nullable=False)
    user = Column(Integer, ForeignKey("users.id"), nullable=False)
    count = Column(Integer, nullable=False)
    time = Column(TIMESTAMP, default=datetime.datetime.now())
    instruments = relationship("Instrument", back_populates="orders")