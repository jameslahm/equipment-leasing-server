from flask import Blueprint

api=Blueprint('api',__name__)

from . import applications,equipments,notifications,users