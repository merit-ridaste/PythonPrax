#import argparse
import gzip
import os
import urllib.parse
import argparse
import GeoIP
from lxml import etree
from lxml.cssselect import CSSSelector
from jinja2 import Environment, FileSystemLoader
import codecs

PROJECT_ROOT = os.path.dirname(__file__)
#root = os.path.expanduser("~/Documents/Python/logs/")
parser= argparse.ArgumentParser(description='Apache2 log parser.')
parser.add_argument('--output',
    help="This is where we place the output files such as report.html and map.svg",
    default='build')
parser.add_argument ('--path', 
    help = "Path to Apache2 log files", default="/var/log/apache2")
parser.add_argument('--top-urls',
    help= "Find top URL-s", action='store_true')
parser.add_argument('--geoip',
    help = "Resolve IP-s to country codes", default="GeoIP.dat")
parser.add_argument('--verbose',
    help = "Increase verbosity", action="store_true")
args= parser.parse_args()

try:
    gi = GeoIP.open(args.geoip, GeoIP.GEOIP_MEMORY_CACHE)
except: 
    print("Failed to open up GeoIP database, are you sure %s exists?" % args.geoip)
    exit(255)

keywords = "Windows", "Linux", "OS X", "Ubuntu", "Googlebot", "bingbot", "Android", "YandexBot", "facebookexternalhit"
d = {}# Curly braces define empty dictionary
urls = {}
user_bytes={}
ip_addresses={}
countries = {}

total = 0


for filename in os.listdir(args.path):
    if not filename.startswith("access.log"):
        #print "Skipping unknown file:", filename
        continue
    if filename.endswith(".gz"):
        continue
        data = gzip.open(os.path.join(args.path, filename))
    else:   
        data= open(os.path.join(args.path,filename), "rb")
    if args.verbose:
        print ("Parsing:", filename)    
    for line in data:
        total += 1
        try:
            source_timestamp, request, response, referrer, _, agent, _ = line.decode("utf-8").split("\"")
            method, path, protocol = request.split(" ")
        except ValueError:
            continue # Skip garbage
        #print ("Source timestamp:", source_timestamp)    
#NEW ADD:
        source_ip, _, _, timestamp = source_timestamp.split(" ", 3)
        #print ("Request came from:", source_ip, "When:", timestamp)    

#TRY_EXCEPT 4 liner        
        #loop for ip_addresses{} has done before loop
       # try:
        #    ip_addresses[source_ip] = ip_addresses[source_ip]=1
        #except:
         #   ip_addresses[source_ip] = 1    

        if not ":" in source_ip: #Skip Ipv6
         #if the key is found, writes + 1 to the dictionary.
            ip_addresses[source_ip] = ip_addresses.get(source_ip, 0) + 1 
            cc= gi.country_code_by_addr(source_ip)
            countries[cc] = countries.get(cc, 0) + 1    
        

        if path == "*": continue # Skip asterisk for path

        _, status_code, content_length, _ = response.split(" ")
        content_length = int(content_length)
        path = urllib.parse.unquote(path)
        
        if path.startswith("/~"):
            username = path[2:].split("/")[0]
            try:
                user_bytes[username] = user_bytes[username] + content_length
            except:
                user_bytes[username] = content_length

        try:
            urls[path] += 1
        except:
            urls[path] = 1
        
        for keyword in keywords:
            if keyword in agent:
                try:
                    d[keyword] += 1
                except KeyError:
                    d[keyword] = 1
                break

def humanize(bytes):
    if bytes <1024:
        return "%d B" % bytes
    elif bytes< 1024**2:
        return "%d kB" % (bytes/1024)
    elif bytes <1024**3:
        return "%d MB" %(bytes/1024**2)
    else:
        return "%d GB" %(bytes/1024**3) 

document =  etree.parse(open(os.path.join(PROJECT_ROOT, 'templates', 'map.svg')))
max_hits = max(countries.values())

for country_code, hits in countries.items():
    if not country_code: continue
    #print (country_code, hex(int((hits*255/max_hits)))[2:])
    
    sel = CSSSelector("#" + country_code.lower())
    for j in sel(document):
        j.set("style", "fill:hsl(%d, 90%%, 70%%);" % (120 - hits * 120 / max_hits))
    
    #Remove children, like Saaremaa
    for i in j.iterfind("{http://www.w3.org/2000/svg}path"):
            i.attrib.pop("class", "")

with open(os.path.join(args.output, "map.svg"), "wb") as data:
    data.write(etree.tostring(document))

env = Environment(
    loader=FileSystemLoader(os.path.join(PROJECT_ROOT,"templates")),
    trim_blocks=True)

#info you see next to the map
context = {
    "map": etree.tostring(document).decode("utf-8"),
    "humanize": humanize, # This is why we use locals() :D
    "url_hits": sorted(urls.items(), key=lambda i:i[1], reverse=True),
    "user_bytes": sorted(user_bytes.items(), key = lambda item:item[1], reverse=True),
}

with codecs.open(os.path.join(args.output, "report.html"), "wb", encoding="utf-8") as fh:
    fh.write(env.get_template("template.html").render(context))

os.system("x-www-browser file://" + os.path.realpath("build/template.html") + " &")
      

print()
print("Top 5 IP addresses:")
results = list(ip_addresses.items())
results.sort(key = lambda item:item[1], reverse=True)
for source_ip, hits in results[:5]:
    print (source_ip, "==>", hits)

print()
print("Top 5 bandwidth hoggers:")
results = list(user_bytes.items())
results.sort(key = lambda item:item[1], reverse=True)
for user, transferred_bytes in results[:5]:
    print (user, "==>", humanize(transferred_bytes))
    
print()
print("Top 5 visited URL-s:")
results = list(urls.items())
results.sort(key = lambda item:item[1], reverse=True)
for path, hits in results[:5]:
    print("http://enos.itcollege.ee" + path, "==>", hits, "(", hits * 100 / total, "%)")

print()
print ("The value of __file__ is:", os.path.realpath(__file__))
print()
print ("The directory of __file__ is:", os.path.realpath(os.path.dirname(__file__)))
