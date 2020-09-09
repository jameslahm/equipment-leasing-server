from crypt import methods
import re
from flask import json
from sqlalchemy.sql.expression import null
from flask.globals import request
from . import api
from ..models import User, Notification
from flask import jsonify, Response


def unauthorized_error():
    return Response(jsonify({"error":"unauthorized"}), 401)


@api.route('/notifications',methods=['GET'])
def get_all():
    current_user = User.verify_auth_token(request.headers.get("Authorization"))
    if not current_user:
        return unauthorized_error()
    page = request.args.get("page",1)
    page_size = request.args.get("page_size", 10)
    all_notifications = Notification.get_notification(current_user, request.args)
    if all_notifications == null:
        return unauthorized_error()
    anslist = []
    for i in range((page-1)*page_size,min(len(all_notifications),page*page_size)):
        anslist.append(all_notifications[i].to_json())
    return Response(jsonify({"notifications":anslist,"total":len(anslist)}))


@api.route('/notifications/<int:id>',methods=['PUT', 'DELETE'])
def notification_operate():
    current_user = User.verify_auth_token(request.headers.get("Authorization"))
    if not current_user:
        return unauthorized_error()
    if request.method == "PUT":
        update = Notification.update_notification(id, current_user, request.form)
        if update == null:
            return unauthorized_error()
        return Response(jsonify(update.to_json()))
    if request.method == "DELETE":
        delete = Notification.delete_notification(id, current_user)
        if delete == null:
            return unauthorized_error()
        return Response(jsonify(delete.to_json()))
