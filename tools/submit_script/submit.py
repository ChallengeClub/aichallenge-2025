
from my_setting import aichallenge_submit_setting
import requests
import json,sys,os

if os.path.isfile(sys.argv[1]):
    print(f"Target File : {sys.argv[1]}")
else:
    print("Please input aichallenge_submit.tar.gz file path")
    sys.exit()

if len(sys.argv) == 3:
    comment = sys.argv[2]
else:
    comment = ""

ses = requests.Session()
st = ses.post(
    "https://aichallenge-board.jsae.or.jp/api/user/login",
    params = {
        "password" : aichallenge_submit_setting.password,
        "username" : aichallenge_submit_setting.username
    }
)

ses.headers.update({'Authorization': 'Bearer ' + json.loads(st.text)["AccessToken"]})

st = ses.post(
    "https://aichallenge-board.jsae.or.jp/api/upload/presigned-url",
    params = {
        "fileName": "aichallenge_submit.tar.gz",
        "fileSize": 977109,
        "fileType": "application/x-gzip",
        "comment": comment
    }
)

upload_url = json.loads(st.text)["presignedUrl"]
with open(sys.argv[1], 'rb') as f:
    response = requests.put(upload_url, data=f)
    if response.status_code == 200:
        print("File uploaded successfully!")
    else:
        print(f"File upload failed with status code: {response.status_code}")
        print(response.text)
