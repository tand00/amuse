#!/usr/bin/python3

import requests
import hashlib
import re
import os
from urllib.request import urlretrieve
import tempfile
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from pypdf import PdfWriter

API_GET_LINK = "https://musescore.com/api/jmuse"

PAGES_REGEX = r'pages(?:&quot;|"):(\d+)'
SONG_REGEX = r'property="og:title" content="([^"]+)"'

EXTS = {
    "mp3" : "mp3",
    "midi": "midi",
    "img": "svg"
}

nl = lambda i = 1: print("\n" * (i-1))
info = lambda x: print(" .", x)
warning = lambda x: print(" /!\\", x)
progress = lambda x: print(" [.]", x)
negative = lambda x: print(" [-]", x)
positive = lambda x: print(" [+]", x)

def generateAuth(id, format, section = 0):
    s = str(id) + format + str(section) + ")82"
    hash = hashlib.md5(bytearray(s, "utf-8"))
    return hash.hexdigest()[0:4]

def getDefaultFolderPath(name):
    return os.getcwd() + "/" + name

def chooseFolder(name):
    default = getDefaultFolderPath(name)
    nl()
    info(f"Default output folder : {default}")
    info("Do you want to change ? (press enter to continue without changing)")
    change = input(" > ").strip()
    nl()
    return change if len(change) > 0 else default

def ensureFolderExists(name):
    if os.path.exists(name):
        return
    os.mkdir(name)

def downloadPart(sess, id, format, folder, name, section = 0):
    auth = generateAuth(id, format, section)
    headers = {"Authorization": auth}
    params = {"id": id, "index": section, "type": format}
    res = sess.get(API_GET_LINK, params = params, headers = headers).json()
    download_url = res["info"]["url"]
    ext = EXTS[format]
    section_annotation = "" if section == 0 else f"-{section}"
    filepath = f"{folder}/{name}-{format}{section_annotation}.{ext}"
    urlretrieve(download_url, filepath)
    return filepath

def mergeSVGsIntoPDF(path, files):
    merger = PdfWriter()
    for svg in files:
        pdf_file = tempfile.TemporaryFile()
        drawing = svg2rlg(svg)
        renderPDF.drawToFile(drawing, pdf_file)
        merger.append(pdf_file)
    merger.write(path)
    merger.close()

def cleanSVGs(files):
    for f in files:
        os.remove(f)

def quit():
    nl()
    negative("Bye !\n")

def main():
    nl()
    info("Ready to rock !\n")

    info("Musescore URL : ")
    url = input(" > ").strip()
    nl()

    id = url.split("/")[-1]

    progress("Loading...")
    sess = requests.session()
    sess.headers.update({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"})
    page = sess.get(url).text
    name = re.search(SONG_REGEX, page)[1]
    pages = int(re.search(PAGES_REGEX, page)[1])

    positive("Processing " + name + f" (id : {id})")
    info(str(pages) + " pages to download...")

    folder = chooseFolder(name)
    ensureFolderExists(folder)

    progress("Downloading MP3...")
    downloadPart(sess, id, "mp3", folder, name)
    positive("Downloaded MP3 !")

    progress("Downloading MIDI...")
    downloadPart(sess, id, "midi", folder, name)
    positive("Downloaded MIDI !")

    progress("Downloading images...")
    images = []
    for section in range(pages):
        f = downloadPart(sess, id, "img", folder, name, section)
        images.append(f)
    positive("Downloaded images !")

    progress("Merging into PDF...")
    pdf_path = f"{folder}/{name}.pdf"
    mergeSVGsIntoPDF(pdf_path, images)
    cleanSVGs(images)
    positive(f"Process finished : {pdf_path}")

try:
    main()
except KeyboardInterrupt:
    nl()
finally:
    quit()