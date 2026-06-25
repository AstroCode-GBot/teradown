from flask import Flask, request, jsonify
from curl_cffi import requests
import re
import urllib.parse


app = Flask(__name__)



def extract_surl(url):

    parsed = urllib.parse.urlparse(url)

    q = urllib.parse.parse_qs(
        parsed.query
    )

    if "surl" in q:
        return q["surl"][0]


    if "/s/" in url:
        return url.split("/s/")[1].split("?")[0]


    return None



def get_size(size):

    try:

        size=int(size)

        if size >= 1024**3:
            return f"{size/1024**3:.2f} GB"

        if size >= 1024**2:
            return f"{size/1024**2:.2f} MB"

        if size >= 1024:
            return f"{size/1024:.2f} KB"

        return f"{size} B"

    except:

        return None




def terabox(url, ndus):


    session=requests.Session(
        impersonate="chrome110"
    )


    session.cookies.update({

        "ndus":ndus

    })


    ua=(
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    " AppleWebKit/537.36 Chrome/145 Safari/537.36"
    )


    surl=extract_surl(url)


    if not surl:

        return {

            "status":False,

            "message":"Invalid url"

        }




    share_url=(
        f"https://dm.terabox.app/"
        f"sharing/link?surl={surl}"
    )



    r=session.get(

        share_url,

        headers={

            "User-Agent":ua

        }

    )



    token=re.search(

        r'fn%28%22(.*?)%22%29',

        r.text

    )



    if not token:


        return {

            "status":False,

            "message":"jsToken missing"

        }



    jsToken=token.group(1)




    params={


        "app_id":"250528",

        "jsToken":jsToken,

        "site_referer":
        "https://www.terabox.app/",

        "shorturl":surl,

        "root":"1"

    }




    headers={


        "User-Agent":ua,


        "Accept":
        "application/json,text/plain,*/*",


        "Referer":share_url,


        "X-Requested-With":
        "XMLHttpRequest",


        "Origin":
        "https://dm.terabox.app"

    }



    api=session.get(


        "https://dm.terabox.app/share/list",


        params=params,

        headers=headers

    )



    try:

        data=api.json()

    except:

        return {

            "status":False,

            "message":"API JSON failed",

            "raw":api.text[:300]

        }




    files=data.get("list")



    if not files:


        return {

            "status":False,

            "message":"No file found",

            "raw":data

        }



    file=files[0]



    return {


        "status":True,


        "name":
        file.get(
            "server_filename"
        ),



        "size":
        get_size(
            file.get(
                "size"
            )
        ),



        "size_bytes":
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
        file.get(
            "dlink"
        ),



        "fs_id":
        file.get(
            "fs_id"
        )

    }




@app.route("/api")

def api():


    url=request.args.get("url")


    ndus=request.args.get("ndus")



    if not url:

        return jsonify({

            "status":False,

            "message":"url missing"

        })



    if not ndus:

        return jsonify({

            "status":False,

            "message":"ndus missing"

        })



    return jsonify(

        terabox(

            url,

            ndus

        )

    )




@app.route("/")

def home():

    return "Terabox API Working"



if __name__=="__main__":

    app.run(

        host="0.0.0.0",

        port=5000

    )
