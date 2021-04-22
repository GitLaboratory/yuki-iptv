'''
Copyright (C) 2021 Astroncia

    This file is part of Astroncia IPTV.

    Astroncia IPTV is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Astroncia IPTV is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Astroncia IPTV.  If not, see <https://www.gnu.org/licenses/>.
'''
import gzip
import datetime
import xml.etree.ElementTree as ET
from data.modules.astroncia.time import print_with_time

def parse_as_xmltv(epg, settings):
    '''Load EPG file'''
    print_with_time("Trying parsing as XMLTV...")
    try:
        tree = ET.ElementTree(ET.fromstring(epg))
    except ET.ParseError:
        tree = ET.ElementTree(ET.fromstring(gzip.decompress(epg)))
    ids = {}
    programmes_epg = {}
    for channel_epg in tree.findall('./channel'):
        for display_name in channel_epg.findall('./display-name'):
            if not channel_epg.attrib['id'] in ids:
                ids[channel_epg.attrib['id']] = []
            ids[channel_epg.attrib['id']].append(display_name.text)
    for programme in tree.findall('./programme'):
        timezone_offset = 0
        try:
            timezone_parse = programme.attrib['start'].split(" ")[1]
            timezone_hours = 3600 * int("{}{}".format(timezone_parse[1], timezone_parse[2]))
            timezone_minutes = 60 * int("{}{}".format(timezone_parse[3], timezone_parse[4]))
            timezone_offset = timezone_hours + timezone_minutes
            if timezone_parse[0] == '-':
                timezone_offset = timezone_offset * -1
        except: # pylint: disable=bare-except
            pass
        start = datetime.datetime.strptime(
            programme.attrib['start'].split(" ")[0], '%Y%m%d%H%M%S'
        ).timestamp()- timezone_offset + (3600 * settings["timezone"])
        stop = datetime.datetime.strptime(
            programme.attrib['stop'].split(" ")[0], '%Y%m%d%H%M%S'
        ).timestamp()- timezone_offset + (3600 * settings["timezone"])
        chans = ids[programme.attrib['channel']]
        for channel_epg_1 in chans:
            day_start = (
                datetime.datetime.now() - datetime.timedelta(days=1)
            ).replace(hour=0, minute=0, second=0).timestamp()- timezone_offset + (3600 * settings["timezone"])
            day_end = (
                datetime.datetime.now() + datetime.timedelta(days=1)
            ).replace(hour=23, minute=59, second=59).timestamp()- timezone_offset + (3600 * settings["timezone"])
            if not channel_epg_1 in programmes_epg:
                programmes_epg[channel_epg_1] = []
            if start > day_start and stop < day_end:
                try:
                    prog_title = programme.find('./title').text
                except: # pylint: disable=bare-except
                    prog_title = ""
                try:
                    prog_desc = programme.find('./desc').text
                except: # pylint: disable=bare-except
                    prog_desc = ""
                programmes_epg[channel_epg_1].append({
                    "start": start,
                    "stop": stop,
                    "title": prog_title,
                    "desc": prog_desc
                })
    return [programmes_epg, ids]
