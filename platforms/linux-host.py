import os
import pexpect
import sys
import logging

logging.basicConfig(level=logging.DEBUG)

def launch_shell():
    shell = pexpect.spawn("bash", logfile=sys.stdout);
    return shell

def launch_app(shell, app):
    ld_library_path = os.environ["LD_LIBRARY_PATH"]
    path = os.environ["PATH"]
    cmd = "sudo env PATH=" + path + " LD_LIBRARY_PATH=" + ld_library_path + \
          " " + app
    shell.send(cmd + "\n");

def launch_virtio_master(app):
    shell = launch_shell()
    app = app + " 1"
    launch_app(shell, app)
    return shell

def launch_virtio_slave(app):
    shell = launch_shell()
    launch_app(shell, app)
    return shell

def expect_app_end(shell):
    prompt = os.environ["PROMPT"]
    if prompt is None:
        prompt = ".*]\$"
    shell.expect(prompt)
    shell.send("echo $?\n")
    shell.expect("\d+")
    exit_code = shell.match.group(0)
    return int(exit_code)

