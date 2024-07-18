import time
import socket
import ssl
import sys
import shelve
import re
import gzip, zlib
import tkinter
import base64, random

from gui import Browser


DEFAULT_FILE = "/Users/akhilgupta/Desktop/personal-projects/ongoing/browser/test.txt"
CACHE_FILE = "cache"

ENTITIES = {
    "&lt;":"<",
    "&gt;":">",
}

def serialize(li):
    return ''.join(str(v) for v in li)

def unchunk(data):
    acc = b""
    i = 0
    while True:
        cl = data.readline().decode().strip("\r\n")
        cl = int(cl, 16)
        c = data.read(cl)
        # print(c)
        acc += c
        data.readline()
        if cl == 0:
            break
    
    return acc
        

supportedSchemes = ["https", "http", 'file', "data", 'view-source']
openSocs = {}

class URL:
    def __init__(self, url):

        try:
            self.sourceOnly = False
            self.url = url
            if len(preSplit := url.split("view-source:", 1)) >= 2:
                self.sourceOnly = True
                url = preSplit[1]

            urlSplitScheme = url.split("://", 1)
            self.scheme = urlSplitScheme[0]

            self.content = self.buf = ""

            if len(urlSplitScheme) < 2:
                urlSplitScheme = url.split(":", 1)
                if urlSplitScheme[0] == "data":
                    self.scheme = "data"
                    urlSecond = urlSplitScheme[1].split(",", 1)
                    self.type = urlSecond[0]
                    self.content = self.buf = urlSecond[1]

            urlSecond = urlSplitScheme[1].split("/", 1)
            urlHost = urlSecond[0].split(":", 1)

            self.port = 80
            self.secure = False
            if self.scheme == "https":
                self.port = 443
                self.secure = True

            self.version = "HTTP/1.1"
            self.host = urlHost[0]
            self.agent = "Toyser"

            if len(urlHost) > 1:
                self.port = int(urlHost[1])
            
            self.path = "/" + urlSecond[1]
            self.redirect = False

            if self.scheme not in supportedSchemes:
                raise Exception("not supported")
        except:
            self.failed = True
            self.content = self.buf = ""

    def createRequest(self):
        request = "GET {path} {version}\r\n".format(path=self.path, version=self.version)
        request += f"Host: {self.host} \r\n"
        request += f"User-Agent: {self.agent} \r\n"
        request += "Connection: close \r\n"
        request += "Accept-Encoding: gzip \r\n"
        request += "\r\n"
        return request
    
    def parseHeaders(self):
        self.headers = {}
        # splits = re.split(b"(\\r\n\r\n?)",self.response.read(), 1)
        # headers = splits[0]
        # headers = headers.decode()
        # for line in headers.split("\r\n"):
        while True:
            line = self.response.readline().decode()
            if line == "\r\n": break
            parts = line.split(":", 1)
            self.headers[parts[0].casefold()] = parts[1].strip()
        # TODO
        emptied = False
        if "transfer-encoding" in self.headers:
            self.content = unchunk(self.response)
            emptied = True
        # print(self.headers)
        if "content-encoding" in self.headers and "gzip" in self.headers["content-encoding"]:
            if (type(self.content) == type("")):
                self.content = self.response.read()
            self.content = gzip.decompress(self.content)
            emptied = True

            # print(self.content)
        if "image" in self.headers["content-type"]:
            with open(f"./images/img{random.randrange(1,100)}.png", "wb") as f:
                f.write(base64.decodebytes(base64.b64encode(self.content)))
            self.content = self.buf = ""
            emptied = True
        
        if emptied:
            self.content =  self.content.decode()
        else:
            self.content = self.response.read().decode()
                

    def recieve(self):
        self.response = self.soc.makefile("rb", newline="\r\n")
        version, code, desc = self.response.readline().decode().split(" ", 2)
        self.parseHeaders()

        if 400 > int(code) >= 300:
            self.redirect = True        
        if 300 > int(code) >= 200:
            if type(cache) != type({}) and "cache-control" in self.headers and (age := self.headers["cache-control"].casefold()) != "no-store":
                if "max-age" in age:
                    age = age.split("=")[1]
                    cache.set(serialize([self.host, self.port, self.path]), (age, time.time(), self.content))


    
    def request(self):

        if hasattr(self, "failed") and self.failed: 
            self.content = self.buf = ""
            return ""
        
        if self.scheme == "file":
            try:
                with open(self.path) as f:
                    self.content = self.buf = f.read()
                    return self.buf
            except:
                self.failed = True
                self.content = self.buf = ""
                return ""

        if self.scheme == "data":
            return self.buf

        if val := cache.get(serialize([self.host, self.port, self.path])):
            self.content = val[-1]
            return self.content


        if (self.host, self.port) in openSocs:
            self.soc = openSocs[(self.host, self.port)]
        else:
            self.soc = socket.socket(
                family= socket.AF_INET, #address family that tells sock how to find the computer, here - internet
                type= socket.SOCK_STREAM,
                proto=socket.IPPROTO_TCP,
            )
            openSocs[(self.host, self.port)] = self.soc
            self.soc.connect((self.host, self.port)) 
            if self.secure:
                context = ssl.create_default_context()
                self.soc = context.wrap_socket(self.soc, server_hostname=self.host)
            self.soc.send(self.createRequest().encode("utf-8"))
            self.recieve()
            self.soc.close()
            return self.content
            

    
    def replace(self):
        for e, r in ENTITIES.items():
            self.buf = self.buf.replace(e, r)
    
    def gather(self):
        self.buf = ""
        in_tag = False
        for c in self.content:
            if c == "<":
                in_tag = True
            elif c == ">":
                in_tag = False
            elif not in_tag:
                self.buf += c

    def setRedir(self,num):
        self.redirectCount = num


    def show(self):

        if hasattr(self, "failed") and self.failed: return ""
        if self.redirect:
            if not hasattr(self, "redirectCount"):
                self.redirectCount = 1
            else:
                self.redirectCount += 1
            return Redirect(self.headers["location"], self.url, self.redirectCount)
        if "http" in self.scheme:
            self.gather()
        self.replace()

        buf = self.buf
        if self.sourceOnly:
            buf = self.content
        print(buf)

        return buf

class Redirect:
    def __init__(self, newUrl, old, redir) -> None:
        if newUrl[0] == "/":
            self.url = URL(old)
            self.url.path = newUrl
        else:
            self.url = URL(newUrl)

        self.url.setRedir(redir)
        # self.url.redirectCount = redir + 1
        print(self.url.redirectCount, redir)
        if self.url.redirectCount < 10:

            # FIXME: this needs self.browser or something
            Browser().load(self.url)
        else:
            raise Exception("redirect loop")
            
class Cache:
    def __init__(self) -> None:
        self.d = shelve.open(CACHE_FILE)

    def clear(self):
        self.d = {}

    def set(self, key, value):
        print("setting", key, value)
        self.d[key] = value

    def get(self, key):
        print("getting cached")
        if key in self.d:
            val =  self.d[key]
            if not (time.time() - val[1] >= float(val[0])):
                return val
            else:
                del self.d[key]
        return None


if __name__ == '__main__':
    url = f"file://{DEFAULT_FILE}"

    cache = Cache()
    # cache = {}
    if len(sys.argv) >= 2:
        url = sys.argv[1]
    
    Browser().load((URL(url)))
    tkinter.mainloop()

    