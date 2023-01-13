from django.shortcuts import render
from rest_framework.decorators import api_view, parser_classes, action
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK, 
    HTTP_201_CREATED, 
    HTTP_405_METHOD_NOT_ALLOWED, 
    HTTP_400_BAD_REQUEST,
    )
from django.http import HttpResponse
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.parsers import FileUploadParser, MultiPartParser, JSONParser
from rest_framework import viewsets
from loguru import logger

from utils.lib.CRQM.CRQM import CRQMClient
from utils.utils import (
    get_script_from_testcase, 
    get_file_content, 
    create_directory_if_not_exist,
    update_script_from_testcase,
    validateFile,
    validateJsonTemplate,
    create_testcases,
    create_one_testcase
    )
from backendviteadmin.settings import MEDIA_ROOT

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
        return Response(cache_value, HTTP_200_OK)
    
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
    cache.set(cache_key, results, 4 * 60 * 60)
    cRQM.disconnect()
    return Response(results, HTTP_200_OK)


class TestscriptViewSet(viewsets.ViewSet):
    
    parser_classes = [JSONParser, MultiPartParser]
    cRQM = CRQMClient(USERNAME, PASSWORD, PROJECT, HOST)
    
    def list(self, request):
        
        return Response(HTTP_200_OK)

    def create(self, request):
        data = request.data

        # create testcase
        if isinstance(data, list): 
            response = create_testcases(RQMclient=self.cRQM, data=data)
        else:
            response = create_one_testcase(RQMclient=self.cRQM, data=data)
            
        # add into cache
        cache_key = 'RQM:get_all:testcase'
        cache_value = cache.get(cache_key)
        if cache_value is not None:
            if isinstance(response, list):
                for res, dat  in zip(response, data):
                    if res['success']:
                        cache_value['data'].append(
                            {
                                "id": res['id'],
                                "name": dat['title']
                            }
                        )
                        cache_value['number'] += 1
            else:
                if response['success']:
                    cache_value['data'].append(
                        {
                            "id": response['id'],
                            "name": data['title']
                        }
                    )
                    cache_value['number'] += 1
            cache.set(cache_key, cache_value, 4 * 60 * 60)
        
        return Response(response)

    def retrieve(self, request, pk=None):
        cache_key = f'RQM:get_testscript:{pk}'
        cache_value = cache.get(cache_key)
        if cache_value is not None:
            return Response(cache_value, HTTP_200_OK)
        
        results = get_script_from_testcase(RQMclient=self.cRQM, id=pk)
        cache.set(cache_key, results, 24 * 60 * 60) # cache for 24 hours
        return Response(results, HTTP_200_OK)

    def update(self, request, pk=None):
        _ = update_script_from_testcase(RQMclient=self.cRQM, id=pk, data=request.data)
        
        # restore testscript cache
        cache_key = f'RQM:get_testscript:{pk}'
        results = request.data
        cache.set(cache_key, results, 24 * 60 * 60)

        # change testcase cache
        cache_key = 'RQM:get_all:testcase'
        cache_value = cache.get(cache_key)
        if cache_value is not None:
            for index, item in enumerate(cache_value['data']):
                if item['id'] == pk:
                    cache_value['data'][index]['name'] = request.data['title']
                    break
            cache.set(cache_key, cache_value, 4 * 60 * 60)
        return Response(HTTP_201_CREATED)

    @action(['POST'], detail=False)
    def validate(self, request):
        if 'file' in request.FILES:
            # deal with file
            up_file = request.FILES['file']
            create_directory_if_not_exist(MEDIA_ROOT)
            with open(MEDIA_ROOT + up_file.name, 'wb+') as destination:
                for chunk in up_file.chunks():
                    destination.write(chunk)
            data = validateFile(MEDIA_ROOT + up_file.name)
        else:
            data = request.data
        
        # validate data    
        if isinstance(data, list):
            for case in data:
                res = validateJsonTemplate(case)
                if res is not True:
                    return Response(res, HTTP_400_BAD_REQUEST)
        elif isinstance(data, dict):
            res = validateJsonTemplate(data)
            if res is not True:
                return Response(res, HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'Invalid data format!'}, HTTP_400_BAD_REQUEST)
        
        return Response({'success': 'PASSED!', 'data': data}, HTTP_201_CREATED)
    
    def partial_update(self, request, pk=None):
        pass

    def destroy(self, request, pk=None):
        pass


# @api_view(['GET', 'PUT', 'POST'])
# @parser_classes([JSONParser, MultiPartParser])
# def testscript(request, id):
#     # retreive data from cache
#     cRQM = CRQMClient(USERNAME, PASSWORD, PROJECT, HOST)

#     if request.method == 'GET':
#         cache_key = f'RQM:get_testscript:{id}'
#         cache_value = cache.get(cache_key)
#         if cache_value is not None:
#             return Response(cache_value, HTTP_200_OK)
        
#         cRQM.login()
#         results = get_script_from_testcase(RQMclient=cRQM, id=id)
#         cache.set(cache_key, results, 24 * 60 * 60) # cache for 24 hours
#         cRQM.disconnect()
#         return Response(results, HTTP_200_OK)
    
#     elif request.method == 'PUT':
#         cRQM.login()    
#         _ = update_script_from_testcase(RQMclient=cRQM, id=id, data=request.data)
        
#         # restore testscript cache
#         cache_key = f'RQM:get_testscript:{id}'
#         results = get_script_from_testcase(RQMclient=cRQM, id=id)
#         cache.set(cache_key, results, 24 * 60 * 60)

#         # change testcase cache
#         cache_key = 'RQM:get_all:testcase'
#         cache_value = cache.get(cache_key)
#         if cache_value is not None:
#             for index, item in enumerate(cache_value['data']):
#                 if item['id'] == id:
#                     cache_value['data'][index]['name'] = request.data['title']
#                     break
#             cache.set(cache_key, cache_value, 4 * 60 * 60)
#         cRQM.disconnect()
#         return Response(HTTP_201_CREATED)
    
#     elif request.method == 'POST':
#         # up_file = request.FILES['file']
#         # for chunk in up_file.chunks():
#         #     print(chunk)
#         print(request.data)
#         return Response(HTTP_201_CREATED)
    
#     else:
#         return Response(HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['GET'])
def downloadFile(request, filename):
    blob = get_file_content(filename)
    file = HttpResponse(blob, content_type='text/plain')
    file['Content-Disposition'] = "attachment; filename=template.json"
    return file


class FileUploadView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request, format=None):
        up_file = request.FILES['file']
        create_directory_if_not_exist(MEDIA_ROOT)
        with open(MEDIA_ROOT + up_file.name, 'wb+') as destination:
            for chunk in up_file.chunks():
                destination.write(chunk)
                
        return Response(up_file.name, HTTP_201_CREATED)