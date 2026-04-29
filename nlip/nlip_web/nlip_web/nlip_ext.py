'''
Extensions to NLIP Server Library that should eventually be folded in. 
'''

import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi import FastAPI
import time
from nlip_server import server
from nlip_sdk import errors as err 
from nlip_sdk import nlip
from nlip_web import env
from dataclasses import dataclass
import uvicorn
import logging
import inspect

@dataclass 
class SessionState: 
    session_data: any
    touched: time.time

'''
A session which can retrieve previous state based on correlators. 
The child class should call set_session_data to store data that will 
be reused across different calls from the client.  
'''
class StatefulSession(server.NLIP_Session):
    
    async def correlated_execute(self, msg: nlip.NLIP_Message) -> nlip.NLIP_Message:
        # Check if the other side has sent a correlator 
        
        other_correlator =  msg.extract_conversation_token()
        session_data = None
        if self.nlip_app is not None and other_correlator is not None: 
            session_data = self.nlip_app.retrieve_session_data(other_correlator)
        
        if session_data is not None:
            self.set_session_data(session_data)
            self.correlator = other_correlator

        rsp_or_coro = self.execute(msg)
        rsp = await rsp_or_coro if inspect.isawaitable(rsp_or_coro) else rsp_or_coro
        
        # On the response, we need to add the correlator 
        # There are three cases: 
        #  The other side has sent a correlator -- which is the one to send back
        #  The other side has not sent a correlator -- send one if set on local side
        #  The other side has not sent a correlator but subclass added a correlator -- do nothing

        existing_token = rsp.extract_conversation_token()
        if other_correlator is not None and session_data is None: 
            rsp.add_conversation_token(other_correlator,True)
        else:  
            if existing_token is None:
                local_correlator = self.get_correlator()
                if local_correlator is not None: 
                    rsp.add_conversation_token(local_correlator)
        self.get_logger().log(logging.INFO, f"sending back {rsp.to_json()}")
        return rsp
    
    def set_session_data(self, session_data:any):
        self.session_data = session_data
     
    def get_session_data(self) -> any:
        if hasattr(self, 'session_data'):
            return self.session_data
        return None

'''
A subclass of SafeStatefulApplication should implement 
create_stateful_session in order to maintain session state. 

'''

class SafeStatefulApplication(server.SafeApplication):
    def __init__(self):
        self.session_dict = dict()
        self.purge_period = 3600

    def retrieve_session_data(self, correlator):
        answer = self.session_dict.get(correlator, None)
        if answer is not None: 
            answer.touched = time.time()
            return answer.session_data
        return None

    def store_session_data(self, correlator, session_data:any):
        self.session_dict[correlator] = SessionState(session_data, time.time())

    def purge_old(self):
        now = time.time()
        for x in self.session_dict.keys():
            if now - self.session_dict[x].touched > self.purge_period:
                # Data has not been touched for an hour - can be removed.
                self.session_dict.pop(x, None)

    '''
    The session state is purged after the purge_period in seconds expires
    The default purge_period is 3600 seconds, or 1 hour. 
    '''
    def set_purge_period(self, purge_period:int):
        self.purge_period = purge_period


    def check_existing(self, request:nlip.NLIP_Message) -> any:
        if request is not None:
            correlator =  request.extract_conversation_token()
            mydata = self.session_dict.get(correlator, None) 
            if mydata is not None:
                return mydata.session_data
        return None

    def remove_session_data(self,session:server.NLIP_Session):
        correlator = session.get_correlator()
        if correlator is not None: 
            entry = self.session_dict.get(correlator,None) 
            if entry is not None:
                self.session_dict[correlator] = None

    def create_session(self) -> server.NLIP_Session:
        session = self.create_stateful_session()
        session.nlip_app = self 
        return session

    def create_stateful_session(self, session_data:any=None) -> StatefulSession:
        raise err.UnImplementedError("create_stateful_session", self.__class__.__name__)
            

class WebApplication(SafeStatefulApplication):
    def __init__(self, indexFile="index.html", pathname = "/static", static_dir="static", favicon_path="/static/NLIPlogo.png"):
        super().__init__()
        self.static_dir = static_dir
        self.favicon_path = favicon_path
        self.indexFile = indexFile
        self.pathname = pathname


    def setup_webserver(self, thisapp:server.NLIP_Application, port, host="localhost") -> FastAPI:
            app = server.setup_server(thisapp)
            app.mount(self.pathname, StaticFiles(directory=self.static_dir))
        
            @app.get("/", response_class=HTMLResponse)
            async def read_root():
                with open(self.indexFile, "r") as f:
                    html_content = f.read()
                return HTMLResponse(content=html_content)

            @app.get("/favicon.ico", include_in_schema=False)
            async def get_favicon():
                return FileResponse(self.favicon_path)

            self.fastapi_app = app
            self.start_server(port,host=host)
            return app

    def start_server(self, port, host="localhost"):
        uvicorn.run(self.fastapi_app, port=port, host=host)