from flask import Flask, request, jsonify
import requests
import re
from urllib.parse import urlparse, parse_qs
import json


app = Flask(__name__)


NDUS = "Y2t6_i7teHuiX-uHDssg3XhTPleotTOyL1Jf5tPV"


session = requests.Session()


HEADERS = {
    "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/135 Safari/537.36",

    "Cookie":
    f"ndus={NDUS}",

    "Accept":
    "application/json,text/plain,*/*"
}



def get_surl(url):

    parsed = urlparse(url)

    q = parse_qs(parsed.query)

    if "surl" in q:
        return q["surl"][0]


    if "/s/" in url:
        return url.split("/s/")[1].split("?")[0]


    return None



def find(text,a,b):

    try:
        return text.split(a)[1].split(b)[0]
    except:
        return None



def get_token(page):

    patterns=[
        r'fn%28%22(.*?)%22%29',
        r'jsToken":"(.*?)"'
    ]


    for p in patterns:

        m=re.search(p,page)

        if m:
            return m.group(1)


    return None




def get_download(data,file):


    # old method

    if file.get("dlink"):

        return file["dlink"]



    # new method

    try:

        fs_id=file["fs_id"]


        uk=data.get("uk")

        shareid=data.get("shareid")


        if not uk or not shareid:

            return None



        url="https://www.1024terabox.com/share/download"


        params={

            "app_id":"250528",

            "web":"1",

            "channel":"dubox",

            "clienttype":"0",

            "uk":uk,

            "shareid":shareid,

            "fid_list":
            json.dumps([fs_id])

        }



        r=session.get(
            url,
            params=params,
            headers=HEADERS
        )


        j=r.json()



        if "dlink" in j:

            return j["dlink"]



        if "list" in j:

            return j["list"][0].get("dlink")


    except Exception as e:

        print(e)



    return None




def tera(url):

    try:


        r=session.get(
            url,
            headers=HEADERS,
            allow_redirects=True,
            timeout=20
        )


        final=r.url


        surl=get_surl(final)


        if not surl:

            return {
                "status":False,
                "message":"surl missing"
            }




        page=session.get(

            f"https://www.1024terabox.com/wap/share/filelist?surl={surl}",

            headers=HEADERS

        ).text



        token=get_token(page)


        if not token:

            return {

                "status":False,

                "message":"token missing"

            }



        api=(

        "https://www.1024terabox.com/share/list?"

        "app_id=250528"

        "&web=1"

        "&channel=dubox"

        "&clienttype=0"

        f"&jsToken={token}"

        f"&shorturl={surl}"

        "&root=1"

        )



        res=session.get(
            api,
            headers=HEADERS
        )



        data=res.json()



        if data.get("errno"):

            return {

                "status":False,

                "message":"share api failed",

                "raw":data

            }



        files=data.get("list")



        if not files:


            return {

                "status":False,

                "message":"file empty"

            }



        file=files[0]



        download=get_download(
            data,
            file
        )



        return {


            "status":True,


            "name":
            file.get(
                "server_filename"
            ),


            "size":
            file.get(
                "size"
            ),


            "fs_id":
            file.get(
                "fs_id"
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



    except Exception as e:


        return {

            "status":False,

            "error":str(e)

        }




@app.route("/api")

def api():

    url=request.args.get("url")


    if not url:

        return jsonify({

            "status":False,

            "message":"url required"

        })


    return jsonify(
        tera(url)
    )




@app.route("/")

def home():

    return "Terabox API Running"



if __name__=="__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )
