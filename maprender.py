from lxml import etree
from lxml.cssselect import CSSSelector

def render_map(fh, countries):
#This is for colouring the map
    document = etree.parse(fh)
    max_hits = max(countries.values())

    for country_code, hits in countries.items():
        if not country_code: 
            continue
    #print (country_code, hex(int((hits*255/max_hits)))[2:])
    
        sel = CSSSelector("#" + country_code.lower())
        for j in sel(document):
            hue= 120 - hits * 120 / max_hits
        
            j.set("style", "fill:hsl(%d, 90%%, 70%%);" % hue)
    
    #Remove children, like Saaremaa
        for i in j.iterfind("{http://www.w3.org/2000/svg}path"):
            i.attrib.pop("class", "")
#return XML corresponding to colour maps as a string
    return etree.tostring(document)