import subprocess
import os
from fastapi import FastAPI
from app.services.database_update_service import DatabaseUpdateService

proc: subprocess.Popen


def start_dramatique_process():
    global proc
    DETACHED_FLAG = 0
    if subprocess._mswindows:  # type: ignore
        DETACHED_FLAG = 0x00000008
    proc = subprocess.Popen(
        "dramatiq --processes=4 --threads=4 app.dramatiq",
        shell=True,
        stdin=None,
        stdout=None,
        stderr=None,
        close_fds=True,
        creationflags=DETACHED_FLAG,
    )
    print("Dramatiq background process started")


def __on_app_started():
    DatabaseUpdateService.upgrade_public_schema()
    if not os.getenv("IS_DOCKER"):
        start_dramatique_process()  


def __on_app_finished():
    global proc
    if proc:
        proc.kill()
        proc.wait()


def setup_event_handlers(app: FastAPI):
    app.add_event_handler("startup", __on_app_started)
    app.add_event_handler("shutdown", __on_app_finished)
