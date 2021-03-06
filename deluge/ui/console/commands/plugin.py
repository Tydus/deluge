#
# plugin.py
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#
#
from optparse import make_option

from deluge.ui.console.main import BaseCommand
from deluge.ui.client import client
import deluge.ui.console.colors as colors
import deluge.component as component
import deluge.configmanager

import re

class Command(BaseCommand):
    """Manage plugins with this command"""
    option_list = BaseCommand.option_list + (
            make_option('-l', '--list', action='store_true', default=False, dest='list',
                        help='lists available plugins'),
            make_option('-s', '--show', action='store_true', default=False, dest='show',
                        help='shows enabled plugins'),
            make_option('-e', '--enable', dest='enable',
                        help='enables a plugin'),
            make_option('-d', '--disable', dest='disable',
                        help='disables a plugin'),
            make_option('-r', '--reload', action='store_true', default=False, dest='reload',
                        help='reload list of available plugins'),
            make_option('-i', '--install', dest='plugin_file',
                        help='install a plugin from an .egg file'),
    )
    usage = "Usage: plugin [ -l | --list ]\n"\
            "       plugin [ -s | --show ]\n"\
            "       plugin [ -e | --enable ] <plugin-name>\n"\
            "       plugin [ -d | --disable ] <plugin-name>\n"\
            "       plugin [ -i | --install ] <plugin-file>\n"\
            "       plugin [ -r | --reload]"

    def handle(self, *args, **options):
        self.console = component.get("ConsoleUI")

        if len(args) == 0 and not any(options.values()):
            self.console.write(self.usage)
            return

        if options["reload"]:
            client.core.pluginmanager.rescan_plugins()
            self.console.write("{!green!}Plugin list successfully reloaded")
            return

        if options["list"]:
            def on_available_plugins(result):
                self.console.write("{!info!}Available Plugins:")
                for p in result:
                    self.console.write("{!input!}  " + p)

            return client.core.get_available_plugins().addCallback(on_available_plugins)

        if options["show"]:
            def on_enabled_plugins(result):
                self.console.write("{!info!}Enabled Plugins:")
                for p in result:
                    self.console.write("{!input!}  " + p)

            return client.core.get_enabled_plugins().addCallback(on_enabled_plugins)

        if options["enable"]:
            def on_available_plugins(result):
                plugins = {}
                for p in result:
                    plugins[p.lower()] = p
                p_args = [options["enable"]] + list(args)

                for arg in p_args:
                    if arg.lower() in plugins:
                        client.core.enable_plugin(plugins[arg.lower()])

            return client.core.get_available_plugins().addCallback(on_available_plugins)

        if options["disable"]:
            def on_enabled_plugins(result):
                plugins = {}
                for p in result:
                    plugins[p.lower()] = p
                p_args = [options["disable"]] + list(args)

                for arg in p_args:
                    if arg.lower() in plugins:
                        client.core.disable_plugin(plugins[arg.lower()])

            return client.core.get_enabled_plugins().addCallback(on_enabled_plugins)

        if options["plugin_file"]:

            filepath = options["plugin_file"]

            import os.path
            import base64
            import shutil

            if not os.path.exists(filepath):
                self.console.write("{!error!}Invalid path: %s" % filepath)
                return


            config_dir = deluge.configmanager.get_config_dir()
            filename = os.path.split(filepath)[1]

            shutil.copyfile(
                filepath,
                os.path.join(config_dir, "plugins", filename))

            client.core.rescan_plugins()

            if not client.is_localhost():
                # We need to send this plugin to the daemon
                filedump = base64.encodestring(open(filepath, "rb").read())
                try:
                    client.core.upload_plugin(filename, filedump)

                    client.core.rescan_plugins()
                except:
                    self.console.write("{!error!}An error occured, plugin was not installed")

            self.console.write("{!green!}Plugin was successfully installed: %s" % filename)


    def complete(self, line):
        return component.get("ConsoleUI").tab_complete_path(line, ext=".egg", sort="name", dirs_first=-1)