with open('/opt/disgraf_hub/main.py', 'r') as f:
    content = f.read()

patch = """
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print("VALIDATION ERROR:", exc.errors())
    print("BODY:", exc.body)
    return JSONResponse(status_code=422, content={"detail": exc.errors()})
"""

if "validation_exception_handler" not in content:
    content = content.replace("app = FastAPI()", "app = FastAPI()\n" + patch)
    with open('/opt/disgraf_hub/main.py', 'w') as f:
        f.write(content)
