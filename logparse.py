#import argparse
import gzip
import os
import urllib.parse
import argparse

#root = os.path.expanduser("~/Documents/Python/logs/")
parser= argparse.ArgumentParser(description='Apache2 log parser.')
parser.add_argument ('--path', 
    help = "Path to Apache2 log files", default="/var/log/apache2")
parser.add_argument('--top-urls',
    help= "Find top URL-s", action='store_true')
parser.add_argument('--geoip',
    help = "Resolve IP-s to country codes", action='store_true')
parser.add_argument('--verbose',
    help = "Increase verbosity", action="store_true")
args= parser.parse_args()

keywords = "Windows", "Linux", "OS X", "Ubuntu", "Googlebot", "bingbot", "Android", "YandexBot", "facebookexternalhit"
d = {}# Curly braces define empty dictionary
urls = {}
user_bytes={}
ip_addresses={}


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
        if not ":" in source_ip:
            ip_addresses[source_ip] = ip_addresses.get(source_ip, 0) + 1 
        #if the key is found, writes + 1 to the dictionary. 



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
