from fastapi import FastAPI
import requests
import os

app = FastAPI()

# 여기에 본인 네이버 API 정보를 넣으세요
NAVER_CLIENT_ID = os.getenv("v2DZ1hkm3QEWF_j3xm8M")
NAVER_CLIENT_SECRET = os.getenv("rxpeP32oSN")


@app.get("/")
def root():
    return {"message": "네이버 검색 서버가 실행 중입니다."}


@app.get("/search/news")
def search_news(query: str):
    url = "https://openapi.naver.com/v1/search/news.json"

    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }

    params = {
        "query": query,
        "display": 3,
        "sort": "sim"
    }

    response = requests.get(url, headers=headers, params=params)
    response.encoding = "utf-8"

    if response.status_code != 200:
        return {
            "error": "네이버 API 호출 실패",
            "status_code": response.status_code,
            "detail": response.text
        }

    data = response.json()

    results = []
    for item in data.get("items", []):
        results.append({
            "title": item.get("title"),
            "description": item.get("description"),
            "link": item.get("link")
        })

    return {
        "query": query,
        "results": results
    }
@app.post("/mcp")
async def mcp_endpoint(request: dict):
    method = request.get("method")
    params = request.get("params", {})

    # MCP 도구 목록 요청
    if method == "tools/list":
        return {
            "tools": [
                {
                    "name": "search_naver_news",
                    "description": "네이버 뉴스 검색",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "검색어"
                            }
                        },
                        "required": ["query"]
                    }
                }
            ]
        }

    # MCP 도구 실행 요청
    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name == "search_naver_news":
            query = arguments.get("query")

            # 기존 함수 재사용
            result = search_news(query)

            return {
                "content": [
                    {
                        "type": "text",
                        "text": str(result)
                    }
                ]
            }

    return {"error": "지원하지 않는 요청"}