import time
import socket
import ssl
import sys
import shelve
import re
import gzip, zlib


DEFAULT_FILE = "/Users/akhilgupta/Desktop/personal-projects/ongoing/browser/test.txt"
CACHE_FILE = "cache"
# https://www.google-analytics.com/analytics.js <- test for cached website
ENTITIES = {
    "&lt;":"<",
    "&gt;":">",
}


def load(url):
    url.request()
    url.show() 

def serialize(li):
    return ''.join(str(v) for v in li)

def unchunk(data):
    acc = b""
    i = 0
    # data = data.replace(b"\x00", b"")
    # data.decode()
    while True:
        cl = data.readline().decode().strip("\r\n")
        cl = int(cl, 16)
        c = data.read(cl)
        # print(c)
        acc += c
        data.readline()
        if cl == 0:
            break
        # print(i)
        # print(data[i:i+1].split(b"x"))
        # cha = int(data[i:i+1],16)
        # print(cha, i+3, i+3+cha, i+3+cha+2)
        # if (cha == 0): break
        # acc += data[i+3:i+3+cha]
        # i = i+3+cha+2
    
    return acc
        
# print(unchunk(b"4\r\nwiki\r\n7\r\npedia i\r\nB\r\nn \r\nchunks.\r\n0\r\n\r\n").decode())


openSocs = {}

class URL:
    def __init__(self, url):

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
            self.headers[parts[0].casefold()] = parts[1]
        # TODO
        # assert "content-encoding" not in self.headers
        # assert "transfer-encoding" not in self.headers
        # if "content-length" not in self.headers:
        #     self.content = "oop"
        # else:
        if "transfer-encoding" in self.headers:
            self.content = unchunk(self.response)
        print(self.headers)
        if "content-encoding" in self.headers and "gzip" in self.headers["content-encoding"]:
            self.content = gzip.decompress(self.content)
            self.content =  self.content.decode()
        else:
            # print(unchunked)
            self.content = self.response.decode()
        # print(splits[-1], "lol")
                

    def recieve(self):
        self.response = self.soc.makefile("rb", newline="\r\n")
        # print(self.response.read())
        version, code, desc = self.response.readline().decode().split(" ", 2)
        self.parseHeaders()

        if 400 > int(code) >= 300:
            self.redirect = True        
        if 300 > int(code) >= 200:
            if "cache-control" in self.headers and (age := self.headers["cache-control"].casefold()) != "no-store":
                if "max-age" in age:
                    age = age.split("=")[1]
                    cache.set(serialize([self.host, self.port, self.path]), (age, time.time(), self.content))


    
    def request(self):
        if self.scheme == "file":
            with open(self.path) as f:
                self.content = self.buf = f.read()
                return self.buf
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
            load(self.url)
        else:
            raise Exception("redirect loop")
            
class Cache:
    def __init__(self) -> None:
        self.d = shelve.open(CACHE_FILE)
    def set(self, key, value):
        print("setting", key, value)
        self.d[key] = value

    def get(self, key):
        return None
        print("getting cached")
        if key in self.d:
            val =  self.d[key]
            if not (time.time() - val[1] >= float(val[0])):
                return val
            else:
                del self.d[key]
        return None

class Browser:
    def __init__(self):
        pass

if __name__ == '__main__':
    url = f"file://{DEFAULT_FILE}"

    cache = Cache()
    if len(sys.argv) >= 2:
        url = sys.argv[1]
    load(URL(url))