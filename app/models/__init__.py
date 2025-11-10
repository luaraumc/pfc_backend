# ===================== DEPENDÊNCIAS SQLALCHEMY CENTRALIZADAS =====================
# Este arquivo centraliza todas as dependências SQLAlchemy para serem utilizadas
# pelos models individuais através de: from . import Base, Column, Integer, etc.

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric, UniqueConstraint, Boolean, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref
from app.dependencies import Base