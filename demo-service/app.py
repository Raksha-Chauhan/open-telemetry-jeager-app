from fastapi import FastAPI, Request
from opentelemetry import trace

app = FastAPI()
tracer = trace.get_tracer(__name__)

@app.get("/")
def read_root():
    # Root span for GET /
    current_span = trace.get_current_span()
    if current_span:
        current_span.set_attribute("endpoint", "/")
    return {"message": "Hello OpenTelemetry with Jaeger!"}

@app.get("/performance")
def hi_endpoint(request: Request):
    return {"message": f"Hi endpoint! Header performance "}

@app.get("/non-performance")
def hi_endpoint(request: Request):
    return {"message": f"Hi endpoint! Header non performance "}
