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
   

def attraction_detail(request, attraction_name):
    # Get the tourist attraction by name from the Oracle database
    attraction = OracleDatabase.fetch_attraction_by_name(attraction_name)

    if attraction:
        # If attraction is found, pass it to the template
        context = {
            'attraction': attraction,
        }
        return render(request, 'tembeakenyasite/attraction_detail.html', context)
    else:
        # If no attraction is found, return an error page or a 404
        return render(request, 'tembeakenyasite/attraction_not_found.html')

def attraction_map(request):
    # Get the tourist attractions data from the Oracle database
    attractions = OracleDatabase.fetch_tourist_attractions()

    # Pass the attractions data to the template
    context = {
        'attractions': attractions,
    }

    # Render the HTML page
    return render(request, 'tembeakenyasite/attractions_map.html', context)
