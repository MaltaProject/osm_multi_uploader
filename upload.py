#! /usr/bin/python3
# vim: fileencoding=utf-8 encoding=utf-8 et sw=4

# Copyright (C) 2009 Jacek Konieczny <jajcus@jajcus.net>
# Copyright (C) 2009 Andrzej Zaborowski <balrogg@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


"""
Uploads complete osmChange 0.3 files.  Use your login (not email) as username.
"""

__version__ = "$Revision: 21 $"

import os
import subprocess
import sys
import traceback
import base64
import codecs
import optparse

import http.client as httplib
import xml.etree.cElementTree as ElementTree
import urllib.parse as urlparse

class HTTPError(Exception):
    pass

class OSM_API(object):
    url = 'http://api06.dev.openstreetmap.org/'
    def __init__(self, url, username = None, password = None):
        if username and password:
            self.username = username
            self.password = password
        else:
            self.username = ""
            self.password = ""
        self.changeset = None
        self.progress_msg = None
        self.url = url

    def __del__(self):
        #if self.changeset is not None:
        #    self.close_changeset()
        pass

    def msg(self, mesg):
        sys.stderr.write("\r%s…                        " % (self.progress_msg))
        sys.stderr.write("\r%s… %s" % (self.progress_msg, mesg))
        sys.stderr.flush()

    def request(self, conn, method, url, body, headers, progress):
        if progress:
            self.msg("making request")
            conn.putrequest(method, url)
            self.msg("sending headers")
            if body:
                conn.putheader('Content-Length', str(len(body)))
            for hdr, value in headers.items():
                conn.putheader(hdr, value)
            self.msg("end of headers")
            conn.endheaders()
            self.msg(" 0%")
            if body:
                start = 0
                size = len(body)
                chunk = size / 100
                if chunk < 16384:
                    chunk = 16384
                while start < size:
                    end = min(size, int(start + chunk))
                    conn.send(body[start:end])
                    start = end
                    self.msg("%2i%%" % (int(start * 100 / size),))
        else:
            self.msg(" ")
            conn.request(method, url, body, headers)

    def _run_request(self, method, url, body = None, progress = 0, content_type = "text/xml"):
        url = urlparse.urljoin(self.url, url)
        purl = urlparse.urlparse(url)
        if purl.scheme != "http":
            raise ValueError("Unsupported url scheme: %r" % (purl.scheme,))
        if ":" in purl.netloc:
            host, port = purl.netloc.split(":", 1)
            port = int(port)
        else:
            host = purl.netloc
            port = None
        url = purl.path
        if purl.query:
            url += "?" + query
        headers = {}
        if body:
            headers["Content-Type"] = content_type

        try_no_auth = 0

        if not try_no_auth and not self.username:
            raise HTTPError(0, "Need a username")

        try:
            self.msg("connecting")
            conn = httplib.HTTPConnection(host, port)
#            conn.set_debuglevel(10)

            if try_no_auth:
                self.request(conn, method, url, body, headers, progress)
                self.msg("waiting for status")
                response = conn.getresponse()

            if not try_no_auth or (response.status == httplib.UNAUTHORIZED and
                    self.username):
                if try_no_auth:
                    conn.close()
                    self.msg("re-connecting")
                    conn = httplib.HTTPConnection(host, port)
#                    conn.set_debuglevel(10)

                creds = self.username + ":" + self.password
                headers["Authorization"] = "Basic " + \
                        base64.b64encode(bytes(creds, "utf8")).decode("utf8")
                        # ^ Seems to be broken in python3 (even the raw
                        # documentation examples don't run for base64)
                self.request(conn, method, url, body, headers, progress)
                self.msg("waiting for status")
                response = conn.getresponse()

            if response.status == httplib.OK:
                self.msg("reading response")
                sys.stderr.flush()
                response_body = response.read()
            else:
                err = response.read()
                raise HTTPError(response.status, "%03i: %s (%s)" % (
                    response.status, response.reason, err), err)
        finally:
            conn.close()
        return response_body

    def create_changeset(self, created_by, comment,source):
        if self.changeset is not None:
            f = open('logFile','w')
            f.write('changeset already opened')
            raise RuntimeError("Changeset already opened")
        self.progress_msg = "   I'm creating the changeset"
        self.msg("")
        root = ElementTree.Element("osm")
        tree = ElementTree.ElementTree(root)
        element = ElementTree.SubElement(root, "changeset")
        ElementTree.SubElement(element, "tag", {"k": "created_by", "v": created_by})
        
        if ( comment ) :
            ElementTree.SubElement(element, "tag", {"k": "comment", "v": comment})

        if ( source ) :
            ElementTree.SubElement(element, "tag", {"k": "source", "v": source})

#       ElementTree.SubElement(element, "tag", {"k": "import", "v": "yes"})
#       ElementTree.SubElement(element, "tag", {"k": "merged", "v": "no - possible duplicates (will be resolved in following changesets)"})
#       ElementTree.SubElement(element, "tag", {"k": "reviewed", "v": "yes"})
#       ElementTree.SubElement(element, "tag", {"k": "revert", "v": "yes"})
#       ElementTree.SubElement(element, "tag", {"k": "bot", "v": "yes"})
#       ElementTree.SubElement(element, "tag", {"k": "url", "v": "http://www.openstreetmap.org/user/nmixter/diary/8218"})

        body = ElementTree.tostring(root, "utf-8")
        reply = self._run_request("PUT", "/api/0.6/changeset/create", body)
        changeset = int(reply.strip())
        self.msg("done. Id: %i" % (changeset))
        sys.stderr.write("\n")
        self.changeset = changeset
       
        f = open('currentChange','w')
        f.write(str(changeset))

    def upload(self, change):
        if self.changeset is None:
            f = open('logFile','w')
            f.write('changeset not opened')
            raise RuntimeError("Changeset not opened")
        self.progress_msg = "   Now I'm sending changes"
        self.msg("")

        # add in changeset tag to all of the elements.
        for operation in change:
            if operation.tag not in ("create", "modify", "delete"):
                continue
            for element in operation:
                element.attrib["changeset"] = str(self.changeset)

        body = ElementTree.tostring(change, "utf-8")
        reply = self._run_request("POST", "/api/0.6/changeset/%i/upload"
                                                % (self.changeset,), body, 1)
        self.msg("done.")
        sys.stderr.write("\n")
        
        return reply

    def close_changeset(self):
        if self.changeset is None:
            f = open('logFile','w')
            f.write('changeset not opened')
            raise RuntimeError("Changeset not opened")
        self.progress_msg = "   Closing"
        self.msg("")
        reply = self._run_request("PUT", "/api/0.6/changeset/%i/close"
                                                    % (self.changeset,))
        self.changeset = None
        self.msg("done, too.")
        sys.stderr.write("\n")

try:
    this_dir = os.path.dirname(__file__)
    version=1

    try:
        version = int(subprocess.Popen(["svnversion", this_dir], stdout = subprocess.PIPE).communicate()[0].strip())
    except:
        version = 1

    parser = optparse.OptionParser(description='Upload Open Street Map OSC files.',usage='upload.py [options] uploadfile1.osc [uploadfile2.osc] ...')
    parser.add_option('-u','--user',help='OSM Username (not email)',dest='user')
    parser.add_option('-p','--password',help='OSM password',dest='password')
    parser.add_option('-m','--comment',help='Sets the changeset comment tag value, required.',dest='comment')
    parser.add_option('--source',help='Sets the changeset source tag value',dest='source')
    parser.add_option('-s','--changeset',help='Changeset ID',dest='changeset',type='int')
    parser.add_option('-n','--start',help='Create a new Changeset and exit',action='store_const',const=1,dest='start',default=0)
    parser.add_option('-t','--skip',help='Skip uploading any elements that have an error.',action='store_const',const=1,dest='skip',default=0)
    parser.add_option('--server',help='URL for upload server (url,test,live), required.')
    (param,filenames) = parser.parse_args()

    if ( not param.server ) :
        parser.print_help()
        print("\n\nerror: --server flag is required.")
        sys.exit(1)
      
    if ( param.server == 'test') :
        param.server = 'http://api06.dev.openstreetmap.org'
    elif (param.server == 'live') :
        param.server = 'http://api.openstreetmap.org'
        
    if ( param.user) :
        login = param.user
    else:
        login = input("OSM login: ")
    if not login:
        sys.exit(1)

    if (param.password) :
        password = param.password
    else:
        password = input("OSM password: ")
    if not password:
        sys.exit(1)
    
    api = OSM_API(param.server,login, password)

    changes = []
    for filename in filenames:

        if not os.path.exists(filename):
            sys.stderr.write("File %r doesn't exist!\n" % (filename,))
            #This error should not occur when using the multi_uploader script
            f = open('logFile','w')
            f.write('No File Found')
            sys.exit(1)

        if not param.start :
            # Should still check validity, but let's save time

            tree = ElementTree.parse(filename)
            root = tree.getroot()
            if root.tag != "osmChange" or (root.attrib.get("version") != "0.3" and
                    root.attrib.get("version") != "0.6"):
                sys.stderr.write("File %s is not a v0.3 osmChange file!\n" % (filename,))
                sys.exit(1)

        if filename.endswith(".osc"):
            diff_fn = filename[:-4] + ".diff.xml"
        else:
            diff_fn = filename + ".diff.xml"
        if os.path.exists(diff_fn):
            sys.stderr.write("Diff file %r already exists, delete it " \
                    "if you're sure you want to re-upload\n" % (diff_fn,))
        
        if filename.endswith(".osc"):
            comment_fn = filename[:-4] + ".comment"
        else:
            comment_fn = filename + ".comment"
        try:
            comment_file = codecs.open(comment_fn, "r", "utf-8")
            comment = comment_file.read().strip()
            comment_file.close()
        except IOError:
            comment = param.comment

        sys.stderr.write("   File: %r\n" % (filename,))
        sys.stderr.write("   Comment: %s\n" % (comment,))

        if param.changeset :
            api.changeset = int(param.changeset)
        else:
            api.create_changeset("upload.py v. %s" % (version,), comment, param.source)
            if param.start :
                print(api.changeset)
                sys.exit(0)
        while 1:
            try:
                diff_file = codecs.open(diff_fn, "w", "utf-8")
                diff = api.upload(root)
                diff_file.write(diff.decode("utf8"))
                diff_file.close()
            except HTTPError as e:
                sys.stderr.write("\n" + e.args[1] + "\n")
                if e.args[0] in [ 404, 409, 412 ]: # Merge conflict
                    # TODO: also unlink when not the whole file has been uploaded
                    # because then likely the server will not be able to parse
                    # it and nothing gets committed
                    os.unlink(diff_fn)
                errstr = e.args[2].decode("utf8")
                if param.skip and e.args[0] == 409 and \
                        errstr.find("Version mismatch") > -1:
                    id = errstr.split(" ")[-1]
                    found = 0
                    for oper in root:
                        todel = []
                        for elem in oper:
                            if elem.attrib.get("id") != id:
                                continue
                            todel.append(elem)
                            found = 1
                        for elem in todel:
                            oper.remove(elem)
                    if not found:
                        sys.stderr.write("\nElement " + id + " not found\n")
                        if not param.changeset:
                            api.close_changeset()
                        sys.exit(1)
                    sys.stderr.write("\nRetrying upload without element " +
                            id + "\n")
                    continue
                if param.skip and e.args[0] == 400 and \
                        errstr.find("Placeholder Way not found") > -1:
                    id = errstr.replace(".", "").split(" ")[-1]
                    found = 0
                    for oper in root:
                        todel = []
                        for elem in oper:
                            if elem.attrib.get("id") != id:
                                continue
                            todel.append(elem)
                            found = 1
                        for elem in todel:
                            oper.remove(elem)
                    if not found:
                        sys.stderr.write("\nElement " + id + " not found\n")
                        if not param.changeset:
                            api.close_changeset()
                        sys.exit(1)
                    sys.stderr.write("\nRetrying upload without element " +
                            id + "\n")
                    continue
                if param.skip and e.args[0] == 412 and \
                        errstr.find(" requires ") > -1:
                    idlist = errstr.split("id in (")[1].split(")")[0].split(",")
                    found = 0
                    delids = []
                    for oper in root:
                        todel = []
                        for elem in oper:
                            for nd in elem:
                                if nd.tag not in [ "nd", "member" ]:
                                    continue
                                if nd.attrib.get("ref") not in idlist:
                                    continue
                                found = 1
                                delids.append(elem.attrib.get("id"))
                                todel.append(elem)
                                break
                        for elem in todel:
                            oper.remove(elem)
                    if not found:
                        sys.stderr.write("\nElement " + str(idlist) +
                                " not found\n")
                        if not param.changeset:
                            api.close_changeset()
                        sys.exit(1)
                    sys.stderr.write("\nRetrying upload without elements " +
                            str(delids) + "\n")
                    continue
                if not param.changeset:
                   api.close_changeset()
                sys.exit(1)
            break
        if not param.changeset:
            api.close_changeset()
except HTTPError as err:
    sys.stderr.write(err.args[1])
    f = open('logFile','w')
    f.write('HTTP Error')
    sys.exit(1)
except Exception as err:
    sys.stderr.write(repr(err) + "\n")
    traceback.print_exc(file=sys.stderr)
    f = open('logFile','w')
    f.write('Generic Error')
    sys.exit(1)
