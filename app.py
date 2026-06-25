import os
import re
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from urllib.parse import urlparse, parse_qs

app = Flask(__name__)
CORS(app)


NDUS = os.getenv("NDUS", "Y2t6_i7teHuiARugl-i1mlsW_r-zj8lB4RZ9ni5A")



HEADERS = {
    "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/135 Safari/537.36",

    "Accept":
    "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",

    "Accept-Language":
    "en-US,en;q=0.9",

    "Referer":
    "https://1024terabox.com/"
}



def headers():

    h = HEADERS.copy()

    if NDUS:
        h["Cookie"] = f"ndus={NDUS}"

    return h



def get_size(size):

    size=int(size)

    if size >= 1024**3:
        return f"{size/1024**3:.2f} GB"

    if size >= 1024**2:
        return f"{size/1024**2:.2f} MB"

    if size >= 1024:
        return f"{size/1024:.2f} KB"

    return f"{size} B"



def extract_surl(url):

    q=parse_qs(urlparse(url).query)

    if "surl" in q:
        return q["surl"][0]


    m=re.search(r"/s/([^/?]+)",url)

    if m:
        return m.group(1)


    return None




def extract_token(html):


    patterns=[

        r'fn%28%22(.*?)%22%29',

        r'jsToken\s*=\s*"([^"]+)"',

        r'jsToken":"([^"]+)"'

    ]


    for p in patterns:

        m=re.search(p,html)

        if m:
            return m.group(1)


    return None





def terabox(url):

    session=requests.Session()

    session.headers.update(headers())


    r=session.get(
        url,
        allow_redirects=True,
        timeout=30
    )


    final_url=r.url


    surl=extract_surl(final_url)


    if not surl:

        raise Exception("surl not found")



    page=session.get(
        f"https://www.1024terabox.com/wap/share/filelist?surl={surl}",
        timeout=30
    )


    html=page.text



    token=extract_token(html)



    if not token:

        raise Exception("jsToken not found")




    params={

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



    api=session.get(

        "https://www.1024terabox.com/share/list",

        params=params,

        timeout=30

    )



    data=api.json()



    if data.get("errno"):

        raise Exception(
            data.get("errmsg","API failed")
        )



    file=data["list"][0]



    return {

        "file_name":
        file.get("server_filename"),

        "size":
        get_size(file.get("size",0)),

        "size_bytes":
        file.get("size"),

        "thumbnail":
        file.get("thumbs",{}).get("url3"),

        "download":
        file.get("dlink")

    }





@app.route("/")

def home():

    return {
        "status":True,
        "message":"Terabox API running"
    }





@app.route("/api",methods=["GET"])

def api():


    url=request.args.get("url")


    if not url:

        return jsonify({

            "status":False,

            "message":"url missing"

        })



    try:

        data=terabox(url)


        return jsonify({

            "status":True,

            "data":data

        })


    except Exception as e:


        return jsonify({

            "status":False,

            "message":str(e)

        })




if __name__=="__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT",5000))
    )
