# ===================== DEPENDÊNCIAS SQLALCHEMY CENTRALIZADAS =====================

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric, UniqueConstraint, Boolean, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref
from app.dependencies import Base