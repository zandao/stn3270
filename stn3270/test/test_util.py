#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################
# Super TN3270 - stn3270 - is a thin layer on top of py3270 that 
# enables a simpler navigation over virtual 3270 connections.
# Copyright (C) 2012 Alexandre Drummond
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
################################################################################

from ConfigParser import SafeConfigParser
from flexmock import flexmock
import json
import logging
import re
from navigator import *
from field import *

def config_parser(filename):
    config = SafeConfigParser()
    config.read(filename)
    config.filename = filename
    return config

class JsonScreenException(Exception):
    pass

class JsonScreen:
    """Stores and retrieves Screens from json files.
    
    :param name: unique screen name
    :type name: string
    """
    def __init__(self, name):
        if re.search(r'\W', name):
            raise JsonScreenException(('Nome inválido para a tela "%s": nome só pode'+
                                       ' ter caracteres alfanuméricos e _.') % name)
        self.name = name
    
    def load(self, config, emulator_mock):
        """Loads screen from file
        
        :param config: screens config file as a configuration parser
        :param emulator_mock: Saul Tigh 3270 Emulator mock used to retrieve
            a screen from it
        :type config: SafeConfigParser
        :type emulator_mock: flexmock(Emulator)
        :return: modified emulator_mock prepared to return screen, buffer and status
        """
        if config.has_section(self.name):
            self.hex = json.loads(config.get(self.name, 'hex'))
            self.ascii = json.loads(config.get(self.name, 'ascii'))
            self.status = json.loads(config.get(self.name, 'status'))
        else:
            raise Exception('Screen "%s" not found.' % self.name)
        emulator_mock.should_receive('exec_command').with_args('Ascii').and_return(self.ascii)
        emulator_mock.should_receive('exec_command').with_args('ReadBuffer(Ascii)').and_return(self.hex)
        emulator_mock.status = self.status
        return emulator_mock
    
    def store(self, config, emulator):
        """Stores a screen to a file
        
        :param config: configuration to store screen to
        :param emulator: Saul Tigh 3270 Emulator used to retrieve
            a screen from it
        :type emulator: Emulator
        :type config: SafeConfigParser
        """
        self.ascii = emulator.exec_command('Ascii').data
        self.hex = emulator.exec_command('ReadBuffer(Ascii)').data
        self.status = emulator.status.__dict__
        
        if not config.has_section(self.name):
            config.add_section(self.name)
        config.set(self.name, 'hex', json.dumps(self.hex))
        config.set(self.name, 'ascii', json.dumps(self.ascii))
        config.set(self.name, 'status', json.dumps(self.status))
        with open(config.filename, 'wb') as configfile:
            config.write(configfile)
        return self

if __name__ == "__main__":
    import optparse
    
    parser = optparse.OptionParser()
    parser.add_option("-z", "--host", 
                      action="store", type="string", dest="host", default="10.3.10.3")
    parser.add_option("-c", "--capture-file", 
                      action="store", type="string", dest="capturefile", default="capture.3270session")
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="debug", default=False)
    (options, args) = parser.parse_args()
    
    logging.basicConfig(format='%(levelname)-8s %(message)s',
                        level=(logging.DEBUG if options.debug else logging.INFO))
    config = config_parser(options.capturefile)
    em = tigh3270.Emulator(True)
    em.connect(options.host)
    
    print "Pressione Ctrl+C para terminar.\n"

    while True:
        try:
            screen_name = raw_input('Nome da tela a capturar: ').strip()
            if not screen_name:
                continue
        except KeyboardInterrupt:
            break
        
        if config.has_section(screen_name):
            try:
                confirmation = raw_input("Nome da tela já existe. Confirma sobrescrita?[y/N] ").strip().upper()
                if confirmation in ['N','']:
                    continue
            except KeyboardInterrupt:
                break
        try:
            screen = JsonScreen(screen_name)
            screen.store(config, em)
        except JsonScreenException, e:
            logging.error(str(e))
            