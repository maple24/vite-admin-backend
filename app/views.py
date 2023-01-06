from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import FileResponse, HttpResponse
from django.core.cache import cache

from utils.CRQM.CRQM import CRQMClient
from utils.CRQM.utils import get_script_from_testcase, get_testscript_template

# Create your views here.

USERNAME = 'ets1szh'
PASSWORD = 'estbangbangde5'
PROJECT = 'Zeekr'
HOST = 'https://rb-alm-20-p.de.bosch.com'


@api_view(['GET'])
def getAll(request, resourceType):
    # retreive data from cache
    cache_key = f'RQM:get_all:{resourceType}'
    cache_value = cache.get(cache_key)
    if cache_value is not None:
        return Response(cache_value)
    
    # request results from RQM server
    cRQM = CRQMClient(USERNAME, PASSWORD, PROJECT, HOST)
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
    cache.set(cache_key, results, 1 * 60 * 60)
    cRQM.disconnect()
    return Response(results)


@api_view(['GET'])
def getTestscript(request, id):
    # retreive data from cache
    cache_key = f'RQM:get_testscript:{id}'
    cache_value = cache.get(cache_key)
    if cache_value is not None:
        return Response(cache_value)
    
    cRQM = CRQMClient(USERNAME, PASSWORD, PROJECT, HOST)
    cRQM.login()
    results = get_script_from_testcase(RQMclient=cRQM, id=id)
    cache.set(cache_key, results, 1 * 60 * 60) # cache for 1 hour
    cRQM.disconnect()
    return Response(results)


@api_view(['GET'])
def downloadTemplate(request):
    blob = get_testscript_template()
    file = HttpResponse(blob, content_type='text/plain')
    file['Content-Disposition'] = "attachment; filename=template.json"
    return file