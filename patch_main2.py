with open('/opt/disgraf_hub/main.py', 'r') as f:
    content = f.read()

patch = """
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    import json
    with open('/opt/disgraf_hub/pydantic_error.log', 'a') as f:
        f.write(json.dumps(exc.errors()) + "\\n")
        try:
            f.write(json.dumps(exc.body) + "\\n")
        except:
            pass
    return JSONResponse(status_code=422, content={"detail": exc.errors()})
"""

# Replace the previous patch
content = content.split("@app.exception_handler(RequestValidationError)")[0] + patch
with open('/opt/disgraf_hub/main.py', 'w') as f:
    f.write(content)
