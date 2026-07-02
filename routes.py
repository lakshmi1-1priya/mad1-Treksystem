#Handling all teh URLS and linking 
from flask import Blueprint, jsonify
main_bp=Blueprint("main",__name__)


@main_bp.route("/")
def index():
    return jsonify({"message": "Trekking Management Application API is running"})