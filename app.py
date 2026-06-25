import os
import re
import requests

from flask import Flask, request, jsonify
from flask_cors import CORS
from urllib.parse import urlparse, parse_qs


app = Flask(__name__)
CORS(app)


DEFAULT_NDUS = os.getenv("NDUS", "")


def get_headers(ndus):

    return {

        "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/135 Safari/537.36",

        "Accept":
        "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",

        "Accept-Language":
        "en-US,en;q=0.9",

        "Referer":
        "https://1024terabox.com/",

        "Cookie":
        f"ndus={ndus}"

    }



def request_url(url, headers):

    r = requests.get(
        url,
        headers=headers,
        allow_redirects=True,
        timeout=40
    )

    return r



def get_surl(url):

    parsed = urlparse(url)

    query = parse_qs(parsed.query)


    if "surl" in query:
        return query["surl"][0]


    match = re.search(
        r"/s/([^/?]+)",
        url
    )

    if match:
        return match.group(1)


    return None




def extract_js_token(html):

    patterns = [

        r'fn%28%22(.*?)%22%29',

        r'jsToken":"(.*?)"',

        r'jsToken\s*=\s*["\'](.*?)["\']'

    ]


    for pattern in patterns:

        m = re.search(
            pattern,
            html
        )

        if m:
            return m.group(1)


    return None





def extract_file(url, ndus):


    headers = get_headers(ndus)


    session = requests.Session()

    session.headers.update(headers)



    first = session.get(
        url,
        allow_redirects=True,
        timeout=40
    )


    final_url = first.url



    surl = get_surl(final_url)



    if not surl:

        raise Exception(
            "surl not found"
        )



    share_page = (

        "https://www.1024terabox.com/"
        "wap/share/filelist?surl="
        + surl

    )



    html = session.get(
        share_page,
        timeout=40
    ).text




    token = extract_js_token(html)



    if not token:

        raise Exception(
            "jsToken not found"
        )




    params = {

        "app_id":"250528",

        "web":"1",

        "channel":"dubox",

        "clienttype":"0",

        "jsToken":token,

        "page":"1",

        "num":"20",

        "by":"name",

        "order":"asc",

        "shorturl":surl,

        "root":"1,"

    }




    api = session.get(

        "https://www.1024terabox.com/share/list",

        params=params,

        timeout=40

    )



    data = api.json()



    if "list" not in data:

        raise Exception(
            data.get(
                "errmsg",
                "API failed"
            )
        )



    file=data["list"][0]



    return {


        "file_name":
        file.get("server_filename"),


        "size":
        file.get("size"),


        "thumbnail":
        file.get("thumbs",{}).get("url3"),


        "download":
        file.get("dlink")

    }





@app.route("/")

def home():

    return jsonify({

        "status":True,

        "message":
        "Terabox API Running"

    })





@app.route("/api")

def api():


    url=request.args.get("url")


    ndus=request.args.get(
        "ndus",
        DEFAULT_NDUS
    )



    if not url:

        return jsonify({

            "status":False,

            "message":
            "url missing"

        })



    if not ndus:

        return jsonify({

            "status":False,

            "message":
            "ndus missing"

        })



    try:


        result=extract_file(
            url,
            ndus
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
