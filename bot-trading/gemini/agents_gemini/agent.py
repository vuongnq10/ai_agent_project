import os

from google.genai import Client
from google.genai.types import (
    HttpOptions,
    GenerateContentConfig,
    ThinkingConfig,
)
import config

GEMINI_MODEL = "gemini-2.5-flash"
API_KEY = config.API_KEY
client = Client(api_key=API_KEY, http_options=HttpOptions(api_version="v1alpha"))


class Agent:
    def __call__(self, contents, tools=None, system_instruction=None):

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=GenerateContentConfig(
                tools=tools,
                thinking_config=ThinkingConfig(include_thoughts=True),
                temperature=0.2,
                seed=42,
                system_instruction=system_instruction,
            ),
        )
        return response


# curl 'https://www.binance.com/bapi/futures/v1/private/future/strategy/place-order' \
#   -H 'accept: */*' \
#   -H 'accept-language: en-US,en;q=0.9,vi;q=0.8,pt;q=0.7,de;q=0.6' \
#   -H 'bnc-uuid: edefd4ff-6970-4bfe-8bd8-bea5bd909f0b' \
#   -H 'clienttype: web' \
#   -H 'content-type: application/json' \
#   -b 'bnc-uuid=edefd4ff-6970-4bfe-8bd8-bea5bd909f0b; changeBasisTimeZone=; BNC_FV_KEY=336c969873f0a80587fd6720ae16cf6d27f42ca7; lang=en; language=en; se_gd=REaCFQRENQVFgMTUBFxUgZZAFHlcXBXUFpQdQUkd1JRVwEVNWVxc1; se_gsd=ZyAlCj9jNTQnMyctISIyMCYEEF1bAAcAUV1KV1RaVlJXHVNT1; BNC-Location=VN; OptanonAlertBoxClosed=2025-07-26T14:41:22.724Z; userPreferredCurrency=USD_USD; _gcl_au=1.1.109302611.1754318878; fiat-prefer-currency=VND; currentAccount=; logined=y; theme=dark; neo-theme=dark; se_sd=hMNVwBQwUAWGRATsGEwwgZZHQUBtaEQV1pVRRVE51hVVwWlNWVZT1; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2216231396%22%2C%22first_id%22%3A%22196b351fc0223e1-0cc3518a6dfc35-1a525636-3686400-196b351fc0338f0%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E5%BC%95%E8%8D%90%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC%22%2C%22%24latest_referrer%22%3A%22https%3A%2F%2Ftestnet.binancefuture.com%2F%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTk2YjM1MWZjMDIyM2UxLTBjYzM1MThhNmRmYzM1LTFhNTI1NjM2LTM2ODY0MDAtMTk2YjM1MWZjMDMzOGYwIiwiJGlkZW50aXR5X2xvZ2luX2lkIjoiMTYyMzEzOTYifQ%3D%3D%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%24identity_login_id%22%2C%22value%22%3A%2216231396%22%7D%2C%22%24device_id%22%3A%22196b351fc0223e1-0cc3518a6dfc35-1a525636-3686400-196b351fc0338f0%22%7D; aws-waf-token=1ade4988-c58f-40f0-b776-7ed26a312e43:BgoApNkDDVsSAAAA:dD7nHX09U2t98xHhtqWB5wh7HUB4pA89CCgvZU6fJ4d/36pzeg3izAGYgZDz60jwMHjOPgWOgkE3/cnlV+Idu3McIORftdeqbCH78qF+IQgUGDxZvP9Sh4JlRkBS5tFgyyfxWV1uh6MON7HkTGE+xyt37uKhbEdkGtK0p2p0zv6bmSs5Xmy9cIlckq9aTdBN+Sw=; _gid=GA1.2.1967274253.1759883499; r20t=web.00CD0DADE4D8863E5E56139FB263B323; r30t=1; cr00=17CB177B236924E94FDB4DF14C79E6E5; d1og=web.16231396.BECB9E2C47F50F2D1E87CAA1718D312D; r2o1=web.16231396.1EE258A52DF69E7E21A37DB19911B99F; f30l=web.16231396.813623E38880CB19D92AA3B5E8E19243; p20t=web.16231396.5580A51A22FB0286542A0E85DC417631; _uetsid=4d3e49b0a51f11f08fd317ebc3bed680; _uetvid=0342a480714211f0b256eb48f4201c37; futures-layout=pro; OptanonConsent=isGpcEnabled=0&datestamp=Fri+Oct+10+2025+07%3A30%3A47+GMT%2B0700+(Indochina+Time)&version=202506.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=84e460f1-a794-43a8-a430-8c2cccf8bdeb&interactionCount=2&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A1%2CC0004%3A1%2CC0002%3A1&AwaitingReconsent=false&intType=1&geolocation=VN%3BSG; BNC_FV_KEY_T=101-QSXuy%2FJ3PE21wYhaGIknhfGiWlltwAyyt8%2FNvIoyio97%2FT7hbUWAdbX4EEGJQPqo%2F838RPh7WoWkFiNa0Cke1g%3D%3D-QLg7yG2O8bGBJAtz7esK3g%3D%3D-ac; BNC_FV_KEY_EXPIRE=1760077847874; _ga=GA1.2.1908840440.1753540883; _ga_3WP50LGEEC=GS2.1.s1760060948$o233$g0$t1760060948$j60$l0$h0' \
#   -H 'csrftoken: 3e0bbb6a51ed976a5260314f1b66f372' \
#   -H 'device-info: eyJzY3JlZW5fcmVzb2x1dGlvbiI6IjE4MDAsMTE2OSIsImF2YWlsYWJsZV9zY3JlZW5fcmVzb2x1dGlvbiI6IjE4MDAsMTA4OCIsInN5c3RlbV92ZXJzaW9uIjoibWFjT1MgMTAuMTUuNyIsImJyYW5kX21vZGVsIjoiZGVza3RvcCBBcHBsZSBNYWNpbnRvc2ggIiwic3lzdGVtX2xhbmciOiJlbi1VUyIsInRpbWV6b25lIjoiR01UKzA3OjAwIiwidGltZXpvbmVPZmZzZXQiOi00MjAsInVzZXJfYWdlbnQiOiJNb3ppbGxhLzUuMCAoTWFjaW50b3NoOyBJbnRlbCBNYWMgT1MgWCAxMF8xNV83KSBBcHBsZVdlYktpdC81MzcuMzYgKEtIVE1MLCBsaWtlIEdlY2tvKSBDaHJvbWUvMTQwLjAuMC4wIFNhZmFyaS81MzcuMzYiLCJsaXN0X3BsdWdpbiI6IlBERiBWaWV3ZXIsQ2hyb21lIFBERiBWaWV3ZXIsQ2hyb21pdW0gUERGIFZpZXdlcixNaWNyb3NvZnQgRWRnZSBQREYgVmlld2VyLFdlYktpdCBidWlsdC1pbiBQREYiLCJjYW52YXNfY29kZSI6IjY3N2Y0M2JiIiwid2ViZ2xfdmVuZG9yIjoiR29vZ2xlIEluYy4gKEFwcGxlKSIsIndlYmdsX3JlbmRlcmVyIjoiQU5HTEUgKEFwcGxlLCBBTkdMRSBNZXRhbCBSZW5kZXJlcjogQXBwbGUgTTMgUHJvLCBVbnNwZWNpZmllZCBWZXJzaW9uKSIsImF1ZGlvIjoiMTI0LjA0MzQ4MTU1ODc2NTA1IiwicGxhdGZvcm0iOiJNYWNJbnRlbCIsIndlYl90aW1lem9uZSI6IkFzaWEvU2FpZ29uIiwiZGV2aWNlX25hbWUiOiJDaHJvbWUgVjE0MC4wLjAuMCAobWFjT1MpIiwiZmluZ2VycHJpbnQiOiIwN2YzNDQwNjg4OWIyODM5ZDEzYzIwM2IzOTQ2Mjc2ZiIsImRldmljZV9pZCI6IiIsInJlbGF0ZWRfZGV2aWNlX2lkcyI6IiJ9' \
#   -H 'fvideo-id: 336c969873f0a80587fd6720ae16cf6d27f42ca7' \
#   -H 'lang: en' \
#   -H 'origin: https://www.binance.com' \
#   -H 'priority: u=1, i' \
#   -H 'referer: https://www.binance.com/en/futures/TIAUSDT' \
#   -H 'sec-ch-ua: "Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"' \
#   -H 'sec-ch-ua-mobile: ?0' \
#   -H 'sec-ch-ua-platform: "macOS"' \
#   -H 'sec-fetch-dest: empty' \
#   -H 'sec-fetch-mode: cors' \
#   -H 'sec-fetch-site: same-origin' \
#   -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36' \
#   -H 'x-passthrough-token;' \
#   -H 'x-trace-id: 14151a85-4f52-4c22-bb75-125588da7440' \
#   -H 'x-ui-request-trace: 14151a85-4f52-4c22-bb75-125588da7440' \
#   --data-raw '{"strategyType":"OTOCO","subOrderList":[{"strategySubId":1,"firstDrivenId":0,"secondDrivenId":0,"side":"SELL","positionSide":"BOTH","symbol":"TIAUSDT","type":"LIMIT","timeInForce":"GTC","quantity":135,"price":"1.475","securityType":"USDT_FUTURES","reduceOnly":false,"clientOrderId":"web_usdt_st_wlh0waiwvouk9g5dnrlq"},{"side":"BUY","positionSide":"BOTH","symbol":"TIAUSDT","securityType":"USDT_FUTURES","firstTrigger":"PLACE_ORDER","firstDrivenOn":"PARTIALLY_FILLED_OR_FILLED","timeInForce":"GTE_GTC","reduceOnly":true,"quantity":135,"strategySubId":2,"firstDrivenId":1,"secondDrivenId":3,"secondDrivenOn":"PARTIALLY_FILLED_OR_FILLED","secondTrigger":"CANCEL_ORDER","stopPrice":"1.438","workingType":"MARK_PRICE","type":"TAKE_PROFIT_MARKET","priceProtect":true},{"side":"BUY","positionSide":"BOTH","symbol":"TIAUSDT","securityType":"USDT_FUTURES","firstTrigger":"PLACE_ORDER","firstDrivenOn":"PARTIALLY_FILLED_OR_FILLED","timeInForce":"GTE_GTC","reduceOnly":true,"quantity":135,"strategySubId":3,"firstDrivenId":1,"secondDrivenId":2,"secondDrivenOn":"PARTIALLY_FILLED_OR_FILLED","secondTrigger":"CANCEL_ORDER","stopPrice":"1.511","workingType":"MARK_PRICE","type":"STOP_MARKET","priceProtect":true}]}'
# https://developers.binance.com/docs/derivatives/usds-margined-futures/trade/rest-api/Place-Multiple-Orders


data_json = {
    "strategyType": "OTOCO",
    "subOrderList": [
        {
            "strategySubId": 1,
            "firstDrivenId": 0,
            "secondDrivenId": 0,
            "side": "SELL",
            "positionSide": "BOTH",
            "symbol": "TIAUSDT",
            "type": "LIMIT",
            "timeInForce": "GTC",
            "quantity": 135,
            "price": "1.475",
            "securityType": "USDT_FUTURES",
            "reduceOnly": False,
            "clientOrderId": "web_usdt_st_wlh0waiwvouk9g5dnrlq",
        },
        {
            "side": "BUY",
            "positionSide": "BOTH",
            "symbol": "TIAUSDT",
            "securityType": "USDT_FUTURES",
            "firstTrigger": "PLACE_ORDER",
            "firstDrivenOn": "PARTIALLY_FILLED_OR_FILLED",
            "timeInForce": "GTE_GTC",
            "reduceOnly": True,
            "quantity": 135,
            "strategySubId": 2,
            "firstDrivenId": 1,
            "secondDrivenId": 3,
            "secondDrivenOn": "PARTIALLY_FILLED_OR_FILLED",
            "secondTrigger": "CANCEL_ORDER",
            "stopPrice": "1.438",
            "workingType": "MARK_PRICE",
            "type": "TAKE_PROFIT_MARKET",
            "priceProtect": True,
        },
        {
            "side": "BUY",
            "positionSide": "BOTH",
            "symbol": "TIAUSDT",
            "securityType": "USDT_FUTURES",
            "firstTrigger": "PLACE_ORDER",
            "firstDrivenOn": "PARTIALLY_FILLED_OR_FILLED",
            "timeInForce": "GTE_GTC",
            "reduceOnly": True,
            "quantity": 135,
            "strategySubId": 3,
            "firstDrivenId": 1,
            "secondDrivenId": 2,
            "secondDrivenOn": "PARTIALLY_FILLED_OR_FILLED",
            "secondTrigger": "CANCEL_ORDER",
            "stopPrice": "1.511",
            "workingType": "MARK_PRICE",
            "type": "STOP_MARKET",
            "priceProtect": True,
        },
    ],
}


test_data = [
    {
        "clientOrderId": "uhOGXvBoVQUk3MLdsaPvNJ",
        "cumQty": "0",
        "cumQuote": "0.0000000",
        "executedQty": "0",
        "orderId": 15498833980,
        "avgPrice": "0.00",
        "origQty": "221",
        "price": "0.9033000",
        "reduceOnly": False,
        "side": "BUY",
        "positionSide": "BOTH",
        "status": "NEW",
        "stopPrice": "0.0000000",
        "symbol": "TIAUSDT",
        "timeInForce": "GTC",
        "type": "LIMIT",
        "origType": "LIMIT",
        "updateTime": 1760152406022,
        "workingType": "CONTRACT_PRICE",
        "priceProtect": False,
        "priceMatch": "NONE",
        "selfTradePreventionMode": "EXPIRE_MAKER",
        "goodTillDate": 0,
        "additional_properties": {},
    },
    {
        "code": -4129,
        "msg": "Time in Force (TIF) GTE can only be used with open positions or open orders. Please ensure that open orders or positions are available.",
        "additional_properties": {},
    },
    {
        "code": -4129,
        "msg": "Time in Force (TIF) GTE can only be used with open positions or open orders. Please ensure that open orders or positions are available.",
        "additional_properties": {},
    },
]
