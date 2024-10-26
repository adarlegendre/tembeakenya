from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse
import cx_Oracle


def index(request):
    template = loader.get_template("tembeakenyasite/index.html")
    context = {
        "sitename": "Karibu Kenya",
    }
    return HttpResponse(template.render(context, request))

def connectingdb():
    dsn_tns = cx_Oracle.makedsn('gort.fit.vutbr.cz', '1521', service_name='orclpdb')
    connection = cx_Oracle.connect(user='xtester1', password='password', dsn=dsn_tns)
    cursor = connection.cursor()
   