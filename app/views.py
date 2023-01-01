from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response

from utils.CRQM.CRQM import CRQMClient

# Create your views here.


@api_view(['GET'])
def getAll(request, resourceType):
    cRQM = CRQMClient("ets1szh", "estbangbangde4", "Zeekr", "https://rb-alm-20-p.de.bosch.com")
    cRQM.login()
    results = {}
    results['data'] = []
    results['success'] = None
    results['message'] = None

    response = cRQM.getAllByResource(resourceType)
    results['success'] = response['success']
    results['message'] = response['message']
    data = response['data']
    for key, value in data.items():
        item = {}
        item['id'] = key
        item['name'] = value
        results['data'].append(item)
    results['number'] = len(data)
    cRQM.disconnect()
    return Response(results)