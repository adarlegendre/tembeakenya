from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse
from .models import OracleDatabase


def index(request):
    connection_status = OracleDatabase.check_connection()
    template = loader.get_template("tembeakenyasite/index.html")
    context = {
        "sitename": connection_status,
    }
    return HttpResponse(template.render(context, request))

def connectingdb():
    dsn_tns = cx_Oracle.makedsn('gort.fit.vutbr.cz', '1521', service_name='orclpdb')
    connection = cx_Oracle.connect(user='xtester1', password='password', dsn=dsn_tns)
    cursor = connection.cursor()
   