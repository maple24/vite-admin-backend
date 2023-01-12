#-*- coding:utf-8 -*-
'''
author: ZHU JIN
date: 2021.12.07
'''
import urllib3
urllib3.disable_warnings()
import requests
import json
import re
import requests.adapters
from requests.adapters import HTTPAdapter
import os
from artifactory import ArtifactoryPath
import time
import sys
import threading
import logging
from contextlib import closing
import tarfile
import zipfile
from tqdm import tqdm
import pytz
from datetime import datetime
import subprocess


class Aritifacoty_Download:
    """
        Dscription: Download software package from artifactory.
        :param server: project path. Default to GAC daily.
        :param auth: user authentifaction. Default to EST account.
        :param dstfolder: local folder of the download destination. Default to None.
    """
    def __init__(self, server, repo_path, auth=('ets1szh', 'estbangbangde4'), dstfolder='Download') -> None:
        self.server = server
        self.auth = auth
        self.dstfolder = dstfolder
        self.repo_path = repo_path
        
        if self.dstfolder is None:
            self.dstfolder = os.path.abspath(__file__)
        elif os.path.exists(self.dstfolder.split('\\')[0]):
            pass
        else:
            self.dstfolder = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.dstfolder)
        if not os.path.exists(self.dstfolder):
            os.mkdir(self.dstfolder)
        logging.basicConfig(level=logging.DEBUG, filename=os.path.join(self.dstfolder, 'multithread_dl.log'), format='%(asctime)s - %(message)s',
                        datefmt='%d-%b-%y %H:%M:%S', filemode='a')
        
    def singlethread_download(self):
        '''[summary: Download with single thread.]

        Args:
            repo_address ([type:str]): [description:absolute repository address]
        '''
        repo_path = os.path.join(self.server, self.repo_path)
        read_data_once = 1024 * 1000
        t_s = time.time()
        arti_path = ArtifactoryPath(repo_path, auth=self.auth, verify=False)
        local_file = self.dstfolder + "\\" + os.path.basename(str(arti_path))
        file_size = round(ArtifactoryPath.stat(arti_path).size / 1024 / 1024, 2)
        print("The file size is: {} MB".format(file_size))
        read_times = 0
        try:
            fi = arti_path.open()
            fo = open(local_file, 'wb')
            print("Downloading the file- {}".format(local_file))
            while True:
                piece = fi.read(read_data_once)
                if piece:
                    fo.write(piece)
                    fo.flush()
                    read_times += 1
                    print("Downloading progress - [{}MB/{}MB]".format(int(read_times),file_size))
                else:
                    print("OK!Download file success - {}".format(local_file))
                    break
        except Exception as e:
            print("error happend in downloading: {}".format(e))
        t_e = time.time()
        print('Finish->time cost: ', t_e - t_s)
        return os.path.join(self.dstfolder, self.repo_path.split('/')[-1])
            
    def multithread_download(self, threads_num=7):
        '''[summary: Download with multiple threads.]

        Args:
            repo_path ([type:str]): [description:absolute repository address]
        '''
        downloader = Multiple_thread_Downloader(threads_num=threads_num)
        t_s = time.time()
        target_file = os.path.join(self.dstfolder, self.repo_path.split('/')[-1])
        if os.path.exists(target_file):
            print('File exists, cancel download')
            sys.exit(1)
        repo_path = os.path.join(self.server, self.repo_path)
        downloader.start(repo_path, self.auth, target_file)
        t_e = time.time()
        print('Finish->time cost: ', t_e - t_s)
        return os.path.join(self.dstfolder, self.repo_path.split('/')[-1])
    
    def get_latest_version(self, branch):
        '''[summary: Get the latest version from Artifactory repository.]

        Args:
            branch_address ([type:str]): [absolute branch address, eg:'gac-avnt-repos/daily/rb-gac-avnt_generic-1.0_maindev']

        Returns:
            [type:str]: [version info]
        '''
        branch_address = os.path.join(self.server, branch)
        branch = branch.split('/')[-1]
        arti_path = ArtifactoryPath(branch_address, auth=self.auth, verify=False)
        latest_week = 1
        latest_pack = 1
        latest_year = 2021
        valid_pack_pattern = branch + "_([0-9]{4}).([0-9]?[0-9]).([0-9]?[0-9])"
        for software_pack in arti_path:
            mat = re.search(valid_pack_pattern, software_pack.name)
            if mat:
                year_num = int(mat.group(1))
                if year_num > latest_year: 
                    latest_year = year_num
        print("find latest year: {}".format(str(latest_year)))
        valid_pack_pattern = branch + "_" + "{}.".format(str(latest_year)) + "([0-9]?[0-9]).([0-9]?[0-9])"
        for software_pack in arti_path:
            mat = re.search(valid_pack_pattern, software_pack.name)
            if mat:
                week_num = int(mat.group(1))
                if week_num > latest_week: 
                    latest_week = week_num
        valid_pack_pattern = branch + "_" + "{}.".format(str(latest_year)) + "{}.".format(latest_week) + "([0-9]?[0-9])"
        print("find latest week: {}".format(str(latest_week)))
        for software_pack in arti_path:
            mat = re.search(valid_pack_pattern, software_pack.name)
            if mat:
                pack_num = int(mat.group(1))
                if pack_num > latest_pack: 
                    latest_pack = pack_num
        print("find latest pack:{}".format(str(latest_pack)))
        
        latest_version = branch.split('/')[-1] + "_" + str(latest_year) + "." + str(latest_week) + "." + str(latest_pack)
        print("the latest version is: {}".format(latest_version))
        
        return latest_version
    
    def decompress(self, dcfolder=None, members=None):
        '''
        Extracts `tar_file` and puts the `members` to `path`.
        If members is None, all members on `tar_file` will be extracted.
        '''
        if dcfolder is None:
            dcfolder = self.dstfolder
        # version = 0
        # if dsfile is None:
        #     for file in os.listdir(self.dstfolder):
        #         if file.endswith('tgz'):
        #             date = file.split('_')[-1].split('.')
        #             count = int(date[0])*100+int(date[1])*10+int(date[2])
        #             if version <= count:
        #                 version = count
        #                 dsfile = file
        dsfile = os.path.join(self.dstfolder, self.repo_path.split('/')[-1])
        if not os.path.exists(dsfile):
            print("Decompress Error!! File is not existed!")
            sys.exit(1)
        if dsfile.split('.')[-1] == 'tgz':
            tar = tarfile.open(dsfile, mode="r:gz")
            print(f"**********Start uncompressing {dsfile}**********")
            if members is None:
                members = tar.getmembers()
            progress = tqdm(members)
            for member in progress:
                tar.extract(member, path=dcfolder)
                progress.set_description(f"Extracting {member.name}")
            tar.close()
            print(f"++++++++++Done uncompressing++++++++++")
        elif dsfile.split('.')[-1] == 'zip':
            zip = zipfile.ZipFile(dsfile, 'r')
            print(f"**********Start uncompressing {dsfile}**********")
            if members is None:
                members = zip.namelist()
            progress = tqdm(members)
            for member in progress:
                zip.extract(member, path=dcfolder)
                progress.set_description(f"Extracting {member}")
            zip.close()
            print(f"++++++++++Done uncompressing++++++++++")
        else:
            print('File type is not supported to decompress.')
        return dcfolder

    def __str__(self) -> str:
        return f"Tool to download from Artifactory."

    def __repr__(self) -> str:
        return f"Aritifacoty_Download({self.server}, {self.auth}, {self.dstfolder})"


class Multiple_thread_Downloader:
    """
    usage:
    downloader=Downloader()
    downloader.start(
        deployPath="http://file.example.com/somedir/filename.ext",
        auth=('admin', 'password')
        target_file="/path/to/file.ext")
    """

    def __init__(self,
                 threads_num=7,
                 chunk_size=1024 * 1024,
                 timeout=60,
                 ):
        """
            initialization
            :param threads_num=5: number of threads created， 5 by default
            :param chunk_size=1024*1024: the chunk size of the stream get request each time
            :param timeout=60: the maximum time waiting, unit is second
        """
        self.threads_num = threads_num
        self.chunk_size = chunk_size
        self.timeout = timeout if timeout != 0 else threads_num

        self.__content_size = 0
        self.__file_lock = threading.Lock()
        self.__threads_status = {}
        self.__crash_event = threading.Event()
        
        requests.adapters.DEFAULT_RETRIES = 2

    def __establish_connect(self, deployPath, auth):
        """
            connection establishment
            :param deployPath: the file path in artifactory
            :param apikey: the verification of the user generated by artifactory
        """
        logging.info("***********Connection establishing......***********")
        artiPath = ArtifactoryPath(deployPath, auth=auth, verify=False)
        hrd = artiPath.open()
        self.__content_size = int(hrd.headers['Content-Length'])
        logging.info(
            "***********Connection established.********** \nThe file size: {}KB**********".format(self.__content_size / 1024))

    def __page_dispatcher(self):
        """
            dispatch the size for each thread to download
        """
        basic_page_size = self.__content_size // self.threads_num
        start_pos = 0
        while start_pos + basic_page_size < self.__content_size:
            yield {
                'start_pos': start_pos,
                'end_pos': start_pos + basic_page_size
            }
            start_pos += basic_page_size + 1
        # the last part remained
        yield {
            'start_pos': start_pos,
            'end_pos': self.__content_size - 1
        }

    def __download(self, deployPath, auth, file, page):
        """
            download method
            :param deployPath: the file path in artifactory
            :param file: the path for local storage
            :param page: dict for indication of the start and end position
            description: for each thread, pointer moves according to size of every patches; for each patch, pointer moves 1 chunksize a time
        """
        # the byte range for the current thread responsible for
        headers = {
            "Range": "bytes={}-{}".format(page["start_pos"], page["end_pos"])
        }
        thread_name = threading.current_thread().name
        # initialize the thread status
        self.__threads_status[thread_name] = {
            "page_size": page["end_pos"] - page["start_pos"],
            "page": page,
            "status": 0,
        }
        try:
            with closing(requests.get(
                    url=deployPath,
                    auth=auth,
                    verify=False,
                    headers=headers,
                    stream=True,
                    timeout=self.timeout,
            )) as response:
                chunk_num = 0
                for data in response.iter_content(chunk_size=self.chunk_size):
                    # write the chunk size bytes to the target file and needs Rlock here
                    with self.__file_lock:
                        # seek the start position to write from
                        file.seek(page["start_pos"])
                        # write datd
                        file.write(data)
                        chunk_num += 1
                        if self.__threads_status[thread_name]['status'] == 0:
                            if page["start_pos"] < page["end_pos"]:
                                print("|- {}  Downloaded: {}MB / {:.2f}MB".format(thread_name, chunk_num, self.__threads_status[thread_name]['page_size'] / 1024 / 1024))
                            else:
                                print("|=> {} Finished.".format(thread_name))
                        elif self.__threads_status[thread_name]['status'] == 1:
                            print("|XXX {} Crushed.".format(thread_name))
                    # the pointer moves forward along withe the writing execution
                    page["start_pos"] += len(data)
                    self.__threads_status[thread_name]["page"] = page

        except requests.RequestException as exception:
            logging.exception("XXX From {}: ".format(exception))
            self.__threads_status[thread_name]["status"] = 1
            self.__crash_event.set()
        print(f"++++++++++++{thread_name} Done download++++++++++++")
        
    def __run(self, deployPath, auth, target_file):
        """
            run the download thread
            :param deployPath: the file path in artifactory
            :param apikey: the verification of the user generated by artifactory
            :param target_file: the path for local storage including the extension
            :param urlhandler: handler for url including redirction or non-exist
        """
        # thread_list = []
        self.__establish_connect(deployPath, auth)
        self.__threads_status["url"] = deployPath
        self.__threads_status["target_file"] = target_file
        self.__threads_status["content_size"] = self.__content_size
        self.__crash_event.clear()
        logging.info("***********The file meta information***********\nURL: {}\nFile Name: {}\nSize: {:.2f}GB".format(
            self.__threads_status["url"],
            self.__threads_status["target_file"],
            self.__threads_status["content_size"] / 1024 / 1024 /1024
        ))
        print("***********Download started***********")
        # handle url
        # url = urlhandler(deployPath)
        with open(target_file, "wb+") as file:
            for page in self.__page_dispatcher():
                threading.Thread(
                    target=self.__download, args=(deployPath, auth, file, page)
                ).start()
                # thd.start()
                # thread_list.append(thd)
            while threading.active_count() > 1:  # 2&3 is set for GUI application
                try:
                    time.sleep(.1)
                except (KeyboardInterrupt, SystemExit):
                    print("Download is terminated!")
                    sys.exit(1)

        # if crash in downloading
        if self.__crash_event.is_set():
            logging.exception("***********Error for downloading!!!************")
            raise Exception("Error for downloading!!!")
        print("***********Download finished***********")

    def start(self, deployPath, auth, target_file):
        """
            start method for running the program
            :param deployPath: the file path in artifactory
            :param apikey: the verification of the user generated by artifactory
            :param target_file the path for local storage including the extension
            :param urlhandler: handler for url including redirction or non-exist
        """
        # the start time
        start_time = time.time()
        self.__run(deployPath, auth, target_file)

        # total tme used for downloading
        span = time.time() - start_time
        logging.info("***********Downloading finished, total time used:{}s, average speed:{:.2f}KB/s***********"
                     .format((span - 0.5), (self.__content_size / 1024 / (span - 0.5))))


def artimonitor(server, repo, pattern, auth=('ets1szh', 'estbangbangde4')):
    session = requests.Session()
    session.mount('http://', HTTPAdapter(max_retries=3))
    session.mount('https://', HTTPAdapter(max_retries=3))
    session.keep_alive = False
    print("Requesting Arti server, please wait...")
    api = 'api/storage/' + repo + '?list&deep=1&listFolders=0&mdTimestamps=0&includeRootPath=0'
    try:
        response = session.get(server+api, auth=auth, verify=False, timeout=60)
    except urllib3.exceptions.ReadTimeoutError:
        print("Request time out!")
        sys.exit(1)
    except requests.exceptions.ProxyError:
        print("Proxy is required!")
        sys.exit(1)
    else:
        print("Done request successfully.")
        data = json.loads(response.text)
    
    t_lastModified = ''
    f_lastModified = ''
    if 'files' in data:
        for file in data['files']:
            if file['lastModified'] > t_lastModified  and re.search(pattern, file['uri']): 
                t_lastModified = file['lastModified']
                f_lastModified = file
    else:
        print("Error message!!Make sure your pattern and repo are correct.")
        sys.exit(1)
    
    if f_lastModified:
        f_lastModified['uri'] =  repo + f_lastModified['uri']
    else:
        print("Response is empty!!")
        sys.exit(1)
    return f_lastModified