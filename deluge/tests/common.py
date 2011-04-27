import os
import sys
import time
import tempfile
from subprocess import Popen, PIPE

import deluge.configmanager
import deluge.log

deluge.log.setupLogger("none")

def set_tmp_config_dir():
    config_directory = tempfile.mkdtemp()
    deluge.configmanager.set_config_dir(config_directory)
    return config_directory

def rpath(*args):
    return os.path.join(os.path.dirname(__file__), *args)

import gettext
import locale
import pkg_resources

# Initialize gettext
try:
    locale.setlocale(locale.LC_ALL, '')
    if hasattr(locale, "bindtextdomain"):
        locale.bindtextdomain("deluge", pkg_resources.resource_filename("deluge", "i18n"))
    if hasattr(locale, "textdomain"):
        locale.textdomain("deluge")
    gettext.bindtextdomain("deluge", pkg_resources.resource_filename("deluge", "i18n"))
    gettext.textdomain("deluge")
    gettext.install("deluge", pkg_resources.resource_filename("deluge", "i18n"))
except Exception, e:
    print e

def start_core():
    CWD = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    DAEMON_SCRIPT = """
import sys
import deluge.main

sys.argv.extend(['-d', '-c', '%s', '-L', 'info'])

deluge.main.start_daemon()
"""
    config_directory = set_tmp_config_dir()
    fp = tempfile.TemporaryFile()
    fp.write(DAEMON_SCRIPT % config_directory)
    fp.seek(0)

    core = Popen([sys.executable], cwd=CWD, stdin=fp, stdout=PIPE, stderr=PIPE)
    while True:
        line = core.stderr.readline()
        if "Factory starting on 58846" in line:
            time.sleep(0.3) # Slight pause just incase
            break
        elif 'Traceback' in line:
            raise SystemExit(
                "Failed to start core daemon. Do \"\"\"%s\"\"\" to see what's "
                "happening" %
                "python -c \"import sys; import tempfile; "
                "config_directory = tempfile.mkdtemp(); "
                "import deluge.main; import deluge.configmanager; "
                "deluge.configmanager.set_config_dir(config_directory); "
                "sys.argv.extend(['-d', '-c', config_directory, '-L', 'info']); "
                "deluge.main.start_daemon()"
            )
    return core
