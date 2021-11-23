import re
import time
import json
import socket
import threading

import settings
from utility import Logger, State

class Session:
    """client-side session - handling connection to server"""
    
    