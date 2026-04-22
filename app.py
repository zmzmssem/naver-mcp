from fastapi import FastAPI, Request, Response
import requests
import os
import json

app = FastAPI()

# Render 등의 환경변수에서 읽음
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")


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
async def mcp_endpoint(request: Request):
    body = await request.json()

    req_id = body.get("id")
    method = body.get("method")
    params = body.get("params", {})

    def success(result):
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": result
        }

    def error(code, message, data=None):
        payload = {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": code,
                "message": message
            }
        }
        if data is not None:
            payload["error"]["data"] = data
        return payload

    # notification은 응답 본문 없이 종료
    if isinstance(method, str) and method.startswith("notifications/"):
        return Response(status_code=204)

    # MCP initialize
    if method == "initialize":
        return success({
            "protocolVersion": "2025-03-26",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "naver-mcp",
                "version": "1.0.0"
            }
        })

    # 도구 목록
    if method == "tools/list":
        return success({
            "tools": [
                {
                    "name": "search_naver_news",
                    "description": "Search Naver news by keyword",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search keyword"
                            }
                        },
                        "required": ["query"]
                    }
                }
            ]
        })

    # 도구 실행
    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name == "search_naver_news":
            query = arguments.get("query", "")
            result = search_news(query)

            return success({
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False)
                    }
                ]
            })

        return error(-32601, "Tool not found", {"tool": tool_name})

    return error(-32601, "Method not found", {"method": method})