from flask import Flask, request, jsonify
import requests
import re
from urllib.parse import urlparse, parse_qs


app = Flask(__name__)


COOKIE = "Y2t6_i7teHuiX-uHDssg3XhTPleotTOyL1Jf5tPV"


HEADERS = {
    "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/135 Safari/537.36",

    "Cookie": f"ndus={COOKIE}",

    "Accept":
    "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}



def get_surl(url):

    u=urlparse(url)

    q=parse_qs(u.query)

    if "surl" in q:
        return q["surl"][0]


    if "/s/" in url:
        return url.split("/s/")[1].split("?")[0]


    return None



def between(text,a,b):

    try:
        return text.split(a)[1].split(b)[0]
    except:
        return None



def terabox(url):

    try:

        session=requests.Session()

        session.headers.update(HEADERS)


        r=session.get(
            url,
            allow_redirects=True,
            timeout=20
        )


        final=r.url


        surl=get_surl(final)


        if not surl:
            return {
                "error":"surl not found"
            }



        page=session.get(
            f"https://www.1024terabox.com/wap/share/filelist?surl={surl}"
        ).text



        jsToken=None


        token=re.search(
            r'fn%28%22(.*?)%22%29',
            page
        )


        if token:
            jsToken=token.group(1)



        if not jsToken:

            jsToken=between(
                page,
                'jsToken":"',
                '"'
            )


        if not jsToken:

            return {
                "error":"token missing"
            }



        api=(
        "https://www.1024terabox.com/share/list?"
        f"app_id=250528"
        f"&web=1"
        f"&channel=dubox"
        f"&clienttype=0"
        f"&jsToken={jsToken}"
        f"&shorturl={surl}"
        f"&root=1"
        )


        data=session.get(api).json()



        if data.get("errno"):

            return {
                "error":data
            }



        files=data.get("list")


        if not files:

            return {
                "error":"file not found"
            }



        file=files[0]



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



    except Exception as e:

        return {

            "status":False,

            "error":str(e)

        }





@app.route("/api",methods=["GET"])
def api():

    url=request.args.get("url")


    if not url:

        return jsonify({
            "status":False,
            "message":"url missing"
        })


    return jsonify(
        terabox(url)
    )




@app.route("/")
def home():

    return "Terabox API Running"



if __name__=="__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )
