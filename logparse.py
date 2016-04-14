import argparse
import gzip
import os
import GeoIP
#import urllib.parse
from maprender import render_map
from jinja2 import Environment, FileSystemLoader
import codecs
from logparserClass import LogParser
from threading import Thread

PROJECT_ROOT = os.path.dirname(__file__)
#root = os.path.expanduser("~/Documents/Python/logs/")
parser= argparse.ArgumentParser(description='Apache2 log parser.')
parser.add_argument('--output',
    help="This is where we place the output files such as report.html and map.svg",
    default='build')
parser.add_argument ('--path', 
    help = "Path to Apache2 log files", default="logs/")
parser.add_argument('--top-urls',
    help= "Find top URL-s", action='store_true')
parser.add_argument('--geoip',
    help = "Resolve IP-s to country codes", default="GeoIP.dat")
parser.add_argument('--verbose',
    help = "Increase verbosity", action="store_true")
parser.add_argument('--skip-compressed',
    help="Skip compressed files", action="store_true")
args= parser.parse_args()
filenames = []

try:
    gi = GeoIP.open(args.geoip, GeoIP.GEOIP_MEMORY_CACHE)
except: 
    print("Failed to open up GeoIP database, are you sure %s exists?" % args.geoip)
    exit(255)

filenames= [i for i in os.listdir(args.path) if i.startswith("acess.")]
logparser = LogParser(gi, keywords = ("Windows", "Linux", "OS X"))

class ParserThread(Thread):
    def run(self):
        while True:
            try:
                filename = filenames.pop()    
            except IndexError:
                break
                if filename.edswith(".gz"):
                    if args.skip_copressed:
                        continue
                    fh= gzip.open(os.path.join(args.path,filename))
                else:
                    fh= open(os.path.join(args.path,filename))
                if args.verbose:
                    print "Parsing:", filename
                logparser.parse_file(fh)                


threads = [ParserThread() for i in range (0, 4)] 
for thread in threads:
    thread.daemon = True
    thread.start() # Start up the threads
for thread in threads:
    thread.join()     

if not logparser.urls:
    print ("No log entries!")
    exit(254)            

def humanize(bytes):
    if bytes <1024:
        return "%d B" % bytes
    elif bytes< 1024**2:
        return "%d kB" % (bytes/1024)
    elif bytes <1024**3:
        return "%d MB" %(bytes/1024**2)
    else:
        return "%d GB" %(bytes/1024**3) 

env = Environment(
    loader=FileSystemLoader(os.path.join(PROJECT_ROOT, "templates")),
    trim_blocks=True)

rendered_map = render_map(
    open(os.path.join(PROJECT_ROOT, 'templates', 'map.svg')),
    logparser.countries)

context = {
    "map_svg": rendered_map,
    "humanize": humanize, # This is why we use locals() :D
    "keyword_hits": sorted(logparser.d.items(), key=lambda i:i[1], reverse=True),
    "url_hits": sorted(logparser.urls.items(), key=lambda i:i[1], reverse=True),
    "user_bytes": sorted(logparser.user_bytes.items(), key = lambda item:item[1], reverse=True),
}

with codecs.open(os.path.join(args.output, "report.html"), "wb", encoding="utf-8") as fh:
    fh.write(env.get_template("template.html").render(context))

    # A more convenient way is to use env.get_template("...").render(locals())
    # locals() is a dict which contains all locally defined variables ;)

os.system("x-www-browser file://" + os.path.realpath("build/report.html") + " &")








