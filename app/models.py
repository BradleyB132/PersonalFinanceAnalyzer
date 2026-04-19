"""
SQLAlchemy models matching the ERD:
- User, Category, Transaction, DescriptionRule, UploadedFile
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Date, ForeignKey, Text, Boolean
)
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    role = Column(String(20), default="user")
    created_at = Column(DateTime, default=datetime.utcnow)

    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan")
    uploaded_files = relationship("UploadedFile", back_populates="user", cascade="all, delete-orphan")
    description_rules = relationship("DescriptionRule", back_populates="user", cascade="all, delete-orphan")
    budget = relationship("Budget", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # null = system category
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="categories")
    transactions = relationship("Transaction", back_populates="category")
    rules = relationship("DescriptionRule", back_populates="category")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    amount = Column(Float, nullable=False)
    description = Column(Text, nullable=False)
    transaction_date = Column(Date, nullable=False)
    uploaded_file_id = Column(Integer, ForeignKey("uploaded_files.id"), nullable=True)
    source = Column(String(20), default="bank")  # bank or credit_card
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")
    uploaded_file = relationship("UploadedFile", back_populates="transactions")


class DescriptionRule(Base):
    __tablename__ = "description_rules"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(200), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # null = global rule
    created_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("Category", back_populates="rules")
    user = relationship("User", back_populates="description_rules")


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_type = Column(String(20), nullable=False)  # bank or credit_card
    file_name = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="uploaded_files")
    transactions = relationship("Transaction", back_populates="uploaded_file")


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    monthly_income = Column(Float, default=0.0)
    priority_categories = Column(Text, default="")  # comma-separated category IDs
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="budget")
