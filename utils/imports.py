from fastapi import FastAPI, WebSocket, WebSocketDisconnect, APIRouter, Header
import uvicorn, asyncio, uuid, threading, json, requests
from pydantic import BaseModel
import os, sqlite3

import base64

import customtkinter as ctk