import os
import re
import json
import requests

from flask import Flask, request, jsonify
from flask_cors import CORS
from urllib.parse import urlparse, parse_qs


app = Flask(__name__)
CORS(app)


DEFAULT_NDUS = os.getenv("NDUS", "")



def headers(ndus):

    return {
        "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/135 Safari/537.36",

        "Accept":
        "application/json, text/plain, */*",

        "Referer":
        "https://1024terabox.com/",

        "Cookie":
        f"ndus={ndus}",

        "Origin":
        "https://1024terabox.com"
    }



def get_surl(url):

    q = parse_qs(urlparse(url).query)

    if "surl" in q:
        return q["surl"][0]


    m = re.search(
        r"/s/([^/?]+)",
        url
    )

    if m:
        return m.group(1)


    return None




def get_token(html):

    patterns = [

        r'fn%28%22(.*?)%22%29',

        r'jsToken":"(.*?)"',

        r'jsToken\s*=\s*"([^"]+)"'

    ]


    for p in patterns:

        x = re.search(
            p,
            html
        )

        if x:
            return x.group(1)


    return None





def terabox_download(url, ndus):

    s = requests.Session()

    h = headers(ndus)

    s.headers.update(h)



    r = s.get(
        url,
        allow_redirects=True,
        timeout=30
    )


    final_url = r.url


    surl = get_surl(final_url)


    if not surl:

        raise Exception(
            "surl not found"
        )



    page = s.get(

        f"https://www.1024terabox.com/wap/share/filelist?surl={surl}",

        timeout=30

    )


    html = page.text



    token = get_token(html)


    if not token:

        raise Exception(
            "jsToken not found"
        )



    params = {


        "app_id":
        "250528",


        "web":
        "1",


        "channel":
        "dubox",


        "clienttype":
        "0",


        "jsToken":
        token,


        "page":
        "1",


        "num":
        "20",


        "shorturl":
        surl,


        "root":
        "1"

    }




    info = s.get(

        "https://www.1024terabox.com/share/list",

        params=params,

        timeout=30

    ).json()



    if "list" not in info:

        raise Exception(
            "file list failed"
        )



    file = info["list"][0]



    fs_id = file.get(
        "fs_id"
    )


    if not fs_id:

        raise Exception(
            "fs_id missing"
        )





    # REAL DOWNLOAD API

    download_params = {


        "app_id":
        "250528",


        "web":
        "1",


        "channel":
        "dubox",


        "clienttype":
        "0",


        "jsToken":
        token,


        "fsidlist":
        json.dumps([fs_id]),


        "sign":
        ""

    }




    dl = s.get(

        "https://www.1024terabox.com/api/download",

        params=download_params,

        timeout=30

    )



    try:

        dl_json = dl.json()

    except:

        dl_json = {}




    download = (

        dl_json.get("dlink")

        or

        file.get("dlink")

    )



    return {


        "name":
        file.get(
            "server_filename"
        ),


        "size":
        file.get(
            "size"
        ),


        "thumbnail":
        file.get(
            "thumbs",
            {}
        ).get(
            "url3"
        ),


        "download":
        download

    }





@app.route("/")

def home():

    return jsonify({

        "status":
        True,

        "message":
        "Terabox API Running"

    })





@app.route("/api")

def api():


    url = request.args.get(
        "url"
    )


    ndus = request.args.get(
        "ndus",
        DEFAULT_NDUS
    )



    if not url:

        return jsonify({

            "status":
            False,

            "message":
            "url missing"

        })



    if not ndus:

        return jsonify({

            "status":
            False,

            "message":
            "ndus missing"

        })



    try:


        data = terabox_download(
            url,
            ndus
        )


        return jsonify({

            "status":
            True,

            "data":
            data

        })



    except Exception as e:


        return jsonify({

            "status":
            False,

            "message":
            str(e)

        })






if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=int(
            os.getenv(
                "PORT",
                5000
            )
        )

    )
