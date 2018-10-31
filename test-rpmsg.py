import os
import pexpect
import sys
import logging
import pytest

logging.basicConfig(level=logging.DEBUG)

@pytest.mark.parametrize("platform", ["linux-host"])
def test_rpmsg_echo(platform):
    sys.path.append(os.path.dirname(__file__) + "/platforms")
    tmodule = __import__(platform)
    ping_app = "rpmsg-echo-ping-shared"
    echo_app = "rpmsg-echo-shared"

    #launch echo first, it is the virtio slave
    echo = tmodule.launch_virtio_slave(echo_app)
    echo.expect("Starting application...")
    ping = tmodule.launch_virtio_master(ping_app)
    ping.expect("Send data to remote core");
    ret = ping.expect(["Test Results: Error count = 0", "ERROR:", \
            "Stopping application"])
    assert ret == 0, "RPMsg ping test failed -- ping."
    ret = echo.expect(["Stopping application", "ERROR:"])
    assert ret == 0, "RPMsg ping test failed -- echo."
    ret = tmodule.expect_app_end(ping)
    assert ret == 0, "RPMsg ping test failed -- ping."
    ret = tmodule.expect_app_end(echo)
    assert ret == 0, "RPMsg ping test failed -- echo."
