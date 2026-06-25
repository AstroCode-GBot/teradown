from flask import Flask, request, jsonify
from curl_cffi import requests
import re
import traceback

app = Flask(__name__)


DEFAULT_NDUS = "Y2YqaCTteHuiU3Ud_MYU7vHoVW4DNBi0MPmg_1tQ"


def get_size(size):
    size = int(size)

    if size >= 1024**3:
        return f"{size / 1024**3:.2f} GB"
    elif size >= 1024**2:
        return f"{size / 1024**2:.2f} MB"
    elif size >= 1024:
        return f"{size / 1024:.2f} KB"

    return f"{size} B"


def extract_surl(url):

    match = re.search(r"surl=([^&]+)", url)

    if match:
        return match.group(1)

    match = re.search(r"/s/([^/?]+)", url)

    if match:
        return match.group(1)

    return None



def tera(url, ndus):

    try:

        surl = extract_surl(url)

        if not surl:
            return {
                "status":False,
                "message":"Invalid Terabox URL"
            }


        short_url = surl[1:] if surl.startswith("1") else surl


        session = requests.Session(
            impersonate="chrome110"
        )


        session.cookies.update({
            "ndus": ndus
        })


        headers={

            "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"

        }


        page_url = (
            f"https://dm.terabox.app/"
            f"sharing/link?surl={short_url}"
        )


        response=session.get(
            page_url,
            headers=headers,
            timeout=20
        )


        if response.status_code != 200:

            return {
                "status":False,
                "message":"page load failed",
                "code":response.status_code
            }



        html=response.text


        token=re.search(
            r'fn%28%22(.*?)%22%29',
            html
        )


        if not token:

            token=re.search(
                r'fn\(\"(.*?)\"\)',
                html
            )


        if not token:

            return {
                "status":False,
                "message":"jsToken not found"
            }


        jsToken=token.group(1)



        api="https://dm.terabox.app/share/list"


        params={

            "app_id":"250528",
            "web":"1",
            "channel":"dubox",
            "clienttype":"0",
            "jsToken":jsToken,
            "shorturl":short_url,
            "root":"1"

        }


        api_headers={

            "User-Agent":headers["User-Agent"],
            "Accept":"application/json, text/plain, */*",
            "Referer":page_url

        }



        result=session.get(
            api,
            params=params,
            headers=api_headers,
            timeout=20
        )


        data=result.json()



        if "list" not in data:

            return {
                "status":False,
                "message":"file not found",
                "raw":data
            }



        file=data["list"][0]



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

            "size_format":
            get_size(
                file.get("size",0)
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
            file.get(
                "dlink"
            )

        }



    except Exception as e:

        traceback.print_exc()

        return {

            "status":False,
            "message":str(e)

        }




@app.route("/")
def home():

    return "Terabox API Running"



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
            "message":"url missing"

        })


    return jsonify(
        tera(
            url,
            ndus
        )
    )



if __name__=="__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )
