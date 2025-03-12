import requests

url = "https://yunwei-help.keytop.cn/helpApi/HelpDoc/getDataByKeyword"
payload = {
    "keyword": "车位状态",
    "pageIndex": 1,
    "pageSize": 20,
    "projectId": 27
}
headers = {
    'token': '5iw61f16wtjh2p46ue38h19tloo5pftw9fupsd7omeyd6b9uj1jyv4pr0ts86hvdozt8apcrbhbahb9giw74o0kt14c0mxzzxfp40wmfqdiaahsxdvaqzvofmmplm2aesjtgk1pt67zpx7bb',
    'userid': '6c2c601eaf9c4babbb0f8b1a6601260c',
    'Content-Type': 'application/json'
}

response = requests.post(url, headers=headers, json=payload)
# print(response.text)

data = response.json().get("data").get("list")
md_list = []
for _ in data:
    title = _.get("text")
    if "接口" not in title:
        md_list.append(_.get("md"))
    else:
        print(f"查询到{title}接口相关内容，跳过引用")
print(len(md_list))
