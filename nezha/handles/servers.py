import os
import sys
import time
import random
import logging
import hashlib
import contextlib

from oslo.config import cfg

from taskflow.patterns import graph_flow as gf
from taskflow.patterns import linear_flow as lf

from taskflow.openstack.common import uuidutils

from taskflow import engines
from taskflow import exceptions as exc
from taskflow import task

from taskflow.persistence import backends
from taskflow.utils import eventlet_utils as e_utils
from taskflow.utils import persistence_utils as p_utils

from nezha import db
from nezha import exception
from nezha.openstack.common.db import exception as db_exc
from nezha.openstack.common import gettextutils as _
from nezha.openstack.common import log as logging


@contextlib.contextmanager
def _slow_down(how_long=0.5):
    try:
        yield how_long
    finally:
        if len(sys.argv) > 1:
            # Only both to do this if user input provided.
            print("** Ctrl-c me please!!! **")
            time.sleep(how_long)


def _print_wrapped(text):
    print("-" * (len(text)))
    print(text)
    print("-" * (len(text)))


def _get_backend():
    backend_uri = 'sqlite:////tmp/nezha.db'

    backend = backends.fetch({'connection': backend_uri})
    backend.get_connection().upgrade()
    return backend

class PrintText(task.Task):
    """Just inserts some text print outs in a workflow."""
    def __init__(self, print_what, no_slow=False):
        content_hash = hashlib.md5(print_what.encode('utf-8')).hexdigest()[0:8]
        super(PrintText, self).__init__(name="Print: %s" % (content_hash))
        self._text = print_what
        self._no_slow = no_slow

    def execute(self):
        if self._no_slow:
            _print_wrapped(self._text)
        else:
            with _slow_down():
                _print_wrapped(self._text)

    def revert(self, *args, **kwargs):
        print "revert PrintText."



class DefineVMSpec(task.Task):
    """Defines a vm specification to be."""
    def __init__(self, name):
        super(DefineVMSpec, self).__init__(provides='vm_spec', name=name)

    def execute(self):
        return {
            'type': 'kvm',
            'disks': 2,
            'vcpu': 1,
            'ips': 1,
            'volumes': 3,
        }

    def revert(self, *args, **kwargs):
        print "revert DefineVMSpec."


class LocateImages(task.Task):
    """Locates where the vm images are."""
    def __init__(self, name):
        super(LocateImages, self).__init__(provides='image_locations',
                                           name=name)

    def execute(self, vm_spec):
        image_locations = {}
        for i in range(0, vm_spec['disks']):
            url = "http://www.yahoo.com/images/%s" % (i)
            image_locations[url] = "/tmp/%s.img" % (i)
        return image_locations

    def revert(self, vm_spec, *args, **kwargs):
        print "revert LocateImages"


class DownloadImages(task.Task):
    """Downloads all the vm images."""
    def __init__(self, name):
        super(DownloadImages, self).__init__(provides='download_paths',
                                             name=name)

    def execute(self, image_locations):
        for src, loc in image_locations.items():
            with _slow_down(1):
                print("Downloading from %s => %s" % (src, loc))
        return sorted(image_locations.values())

    def revert(self, image_locations, *args, **kwargs):
        print "revert DownloadImages"

class CreateNetworkTpl(task.Task):
    """Generates the network settings file to be placed in the images."""
    SYSCONFIG_CONTENTS = """DEVICE=eth%s
BOOTPROTO=static
IPADDR=%s
ONBOOT=yes"""

    def __init__(self, name):
        super(CreateNetworkTpl, self).__init__(provides='network_settings',
                                               name=name)

    def execute(self, ips):
        settings = []
        for i, ip in enumerate(ips):
            settings.append(self.SYSCONFIG_CONTENTS % (i, ip))
        return settings

    def revert(self, ips, *args, **kwargs):
        print "revert CreateNetworkTpl"


class AllocateIP(task.Task):
    """Allocates the ips for the given vm."""
    def __init__(self, name):
        super(AllocateIP, self).__init__(provides='ips', name=name)

    def execute(self, vm_spec):
        ips = []
        for i in range(0, vm_spec.get('ips', 0)):
            ips.append("192.168.0.%s" % (random.randint(1, 254)))
        return ips

    def revert(self, vm_spec, *args, **kwargs):
        print "revert AllocateIP"


class WriteNetworkSettings(task.Task):
    """Writes all the network settings into the downloaded images."""
    def execute(self, download_paths, network_settings):
        for j, path in enumerate(download_paths):
            with _slow_down(1):
                print("Mounting %s to /tmp/%s" % (path, j))
            for i, setting in enumerate(network_settings):
                filename = ("/tmp/etc/sysconfig/network-scripts/"
                            "ifcfg-eth%s" % (i))
                with _slow_down(1):
                    print("Writing to %s" % (filename))
                    print(setting)

    def revert(self, download_paths, network_settings, *args, **kwargs):
        print "revert WriteNetworkSettings"


class BootVM(task.Task):
    """Fires off the vm boot operation."""
    def execute(self, vm_spec):
        print("Starting vm and would be false!")
        with _slow_down(1):
            print("Created: %s" % (vm_spec))
            raise  IOError("Disk error.....")


class AllocateVolumes(task.Task):
    """Allocates the volumes for the vm."""
    def execute(self, vm_spec):
        volumes = []
        for i in range(0, vm_spec['volumes']):
            with _slow_down(1):
                volumes.append("/dev/vda%s" % (i + 1))
                print("Allocated volume %s" % volumes[-1])
        return volumes

    def revert(self, vm_spec, *args, **kwargs):
        print "revert AllocateVolumes"


class FormatVolumes(task.Task):
    """Formats the volumes for the vm."""
    def execute(self, volumes):
        for v in volumes:
            print("Formatting volume %s" % v)
            with _slow_down(1):
                pass
            print("Formatted volume %s" % v)

    def revert(self, volumes, *args, **kwargs):
        print "revert FormatVolumes"


def create_flow():
    # Setup the set of things to do.
    flow = lf.Flow("root").add(
        PrintText("Starting vm creation.", no_slow=True),
        lf.Flow('vm-maker').add(
            # First create a specification for the final vm to-be.
            DefineVMSpec("define_spec"),
            # This does all the image stuff.
            gf.Flow("img-maker").add(
                LocateImages("locate_images"),
                DownloadImages("download_images"),
            ),
            # This does all the network stuff.
            gf.Flow("net-maker").add(
                AllocateIP("get_my_ips"),
                CreateNetworkTpl("fetch_net_settings"),
                WriteNetworkSettings("write_net_settings"),
            ),
            # This does all the volume stuff.
            gf.Flow("volume-maker").add(
                AllocateVolumes("allocate_my_volumes", provides='volumes'),
                FormatVolumes("volume_formatter"),
            ),
            # Finally boot it all.
            BootVM("boot-it"),
        ),
        # Ya it worked!
        PrintText("Finished vm create.", no_slow=True),
        PrintText("Instance is running!", no_slow=True))
    return flow
    
def get_server(server_id, ctxt=None):
    return db.server_get(ctxt, server_id)

def create_server(values, ctxt=None):
    _print_wrapped("Initializing")
    
    # Setup the persistence & resumption layer.
    backend = _get_backend()

    book_id = None
    flow_id = None
    
    # Set up how we want our engine to run, serial, parallel...
    engine_conf = {
        'engine': 'parallel',
    }
    if e_utils.EVENTLET_AVAILABLE:
        engine_conf['executor'] = e_utils.GreenExecutor(5)

    book = p_utils.temporary_log_book(backend)
    engine = engines.load_from_factory(create_flow,
                                       backend=backend, book=book,
                                       engine_conf=engine_conf)
    
    # Make me my vm please!
    _print_wrapped('Running')
    engine.run()

    return values
