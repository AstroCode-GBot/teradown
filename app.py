import os
import re
import json
import requests

from flask import Flask, request, jsonify
from flask_cors import CORS
from urllib.parse import urlparse, parse_qs


app = Flask(__name__)
CORS(app)


NDUS_DEFAULT = os.getenv("NDUS", "")



def get_headers(cookie):

    return {

        "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/135 Safari/537.36",

        "Accept":
        "application/json, text/plain, */*",

        "Accept-Language":
        "en-US,en;q=0.9",

        "Referer":
        "https://www.1024terabox.com/",

        "Cookie":
        f"ndus={cookie}",

        "Origin":
        "https://www.1024terabox.com"

    }





def get_surl(url):

    q=parse_qs(
        urlparse(url).query
    )


    if "surl" in q:
        return q["surl"][0]


    m=re.search(
        r"/s/([^/?]+)",
        url
    )


    if m:
        return m.group(1)


    return None





def find_token(html):

    patterns=[

        r'fn%28%22(.*?)%22%29',

        r'jsToken":"(.*?)"',

        r'jsToken\s*=\s*"([^"]+)"'

    ]


    for p in patterns:

        m=re.search(
            p,
            html
        )

        if m:
            return m.group(1)


    return None





def get_data(url,cookie):


    s=requests.Session()

    s.headers.update(
        get_headers(cookie)
    )


    page=s.get(

        url,

        allow_redirects=True,

        timeout=40

    )


    final_url=page.url


    surl=get_surl(final_url)


    if not surl:

        raise Exception(
            "surl not found"
        )



    share_page=(

        "https://www.1024terabox.com/"
        "wap/share/filelist?surl="
        +surl

    )


    html=s.get(
        share_page,
        timeout=40
    ).text



    token=find_token(html)


    if not token:

        raise Exception(
            "token missing"
        )





    params={


        "app_id":"250528",

        "web":"1",

        "channel":"dubox",

        "clienttype":"0",

        "jsToken":token,

        "page":"1",

        "num":"20",

        "shorturl":surl,

        "root":"1"

    }




    info=s.get(

        "https://www.1024terabox.com/share/list",

        params=params,

        timeout=40

    ).json()



    if not info.get("list"):

        raise Exception(
            "file not found"
        )



    file=info["list"][0]



    fs_id=file.get("fs_id")

    uk=file.get("uk")

    shareid=file.get("shareid")





    # Direct link API


    download_params={


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


        "uk":
        uk,


        "shareid":
        shareid

    }



    dl=s.get(

        "https://www.1024terabox.com/share/download",

        params=download_params,

        timeout=40

    )



    try:

        dl_json=dl.json()

    except:

        dl_json={}




    download=None



    if dl_json.get("dlink"):

        download=dl_json["dlink"]


    elif dl_json.get("list"):

        download=dl_json["list"][0].get("dlink")




    return {


        "file_name":
        file.get("server_filename"),


        "size":
        file.get("size"),


        "thumbnail":
        file.get("thumbs",{}).get("url3"),


        "download":
        download,


        "debug":
        dl_json

    }







@app.route("/")

def home():

    return jsonify({

        "status":True,

        "message":
        "Terabox API Online"

    })







@app.route("/api")

def api():


    url=request.args.get("url")


    cookie=request.args.get(

        "ndus",

        NDUS_DEFAULT

    )



    if not url:

        return jsonify({

            "status":False,

            "message":
            "URL missing"

        })



    if not cookie:

        return jsonify({

            "status":False,

            "message":
            "NDUS missing"

        })



    try:


        result=get_data(
            url,
            cookie
        )


        return jsonify({

            "status":True,

            "data":result

        })



    except Exception as e:


        return jsonify({

            "status":False,

            "message":str(e)

        })







if __name__=="__main__":

    app.run(

        host="0.0.0.0",

        port=int(
            os.getenv(
                "PORT",
                5000
            )
        )

    )
