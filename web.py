import GeoIP
import os
import gzip
import humanize
from flask import Flask, request
from maprender import render_map
from jinja2 import Environment, FileSystemLoader
from logparserClass import LogParser

PROJECT_ROOT = os.path.dirname(__file__)

gi = GeoIP.open("GeoIP.dat", GeoIP.GEOIP_MEMORY_CACHE)
keywords = "Windows", "Linux", "OS X", "Ubuntu", "Googlebot", "bingbot", "Android", "YandexBot", "facebookexternalhit"


env = Environment(
    loader=FileSystemLoader(os.path.join(PROJECT_ROOT, "templates")),
    trim_blocks=True)

app = Flask(__name__)

def list_log_files():
    """
    This is simply used to filter the files in the logs directory
    """
    for filename in os.listdir("logs/"):
        if filename.startswith("access"):
            yield filename


@app.route("/report/")
#annab flaskile ette kuidas lugeda url'i ja mida sealt välja lugeda. 
def report():
    # Create LogParser instance for this report
    logparser=LogParser(gi, keywords)

    filename = request.args.get("filename")
    if "/" in filename: # Prevent directory traversal attacks
        return "Go away!"

    path = os.path.join("logs/", filename)
    logparser.parse_file(gzip.open(path) if path.endswith(".gz") else open(path, "rb"))

    return env.get_template("template.html").render({
            "map_svg": render_map(open(os.path.join(PROJECT_ROOT, "templates", "map.svg")), logparser.countries),
            "humanize": humanize.naturalsize,
            "keyword_hits": sorted(logparser.d.items(), key=lambda i:i[1], reverse=True),
            "url_hits": sorted(logparser.urls.items(), key=lambda i:i[1], reverse=True),
            "user_bytes": sorted(logparser.user_bytes.items(), key = lambda item:item[1], reverse=True)
        })

@app.route("/")
def index():
    return env.get_template("index.html").render(
        log_files=list_log_files())


if __name__ == '__main__':
    app.run(debug=True)
    