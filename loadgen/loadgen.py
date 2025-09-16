import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

DEMO_SERVICE_URL = "http://demo-service:8000"  # inside docker compose network
JAEGER_QUERY_URL = "http://jaeger:16686/api/traces?service=demo-service"

def wait_for_service(url, retries=20, delay=1):
    for i in range(retries):
        try:
            r = requests.get(f"{url}/", timeout=2)
            if r.status_code == 200:
                print(f"✅ Service ready after {i+1} attempt(s)")
                return True
        except Exception:
            pass
        print(f"⏳ Waiting for service... ({i+1}/{retries})")
        time.sleep(delay)
    print("❌ Service not reachable")
    return False


def send_single_request(endpoint: str, headers: dict, label: str):
    """Send a single HTTP request and return the label if success"""
    try:
        resp = requests.get(f"{DEMO_SERVICE_URL}{endpoint}", headers=headers, timeout=5)
        if resp.status_code == 200:
            return label
    except Exception:
        return None
    return None


def send_requests():
    totals = {"performance": 0, "non-performance": 0}
    print("🚀 Starting parallel load generation...")

    tasks = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        # Launch 100 /performance requests with header x-test-request=performance
        for _ in range(100):
            tasks.append(
                executor.submit(
                    send_single_request,
                    "/performance",
                    {"x_test_request": "performance"},
                    "performance",
                )
            )

        # Launch 100 /non-performance requests with header x-test-request=non-performance
        for _ in range(100):
            tasks.append(
                executor.submit(
                    send_single_request,
                    "/non-performance",
                    {"x_test_request": "non-performance"},
                    "non-performance",
                )
            )

        for future in as_completed(tasks):
            result = future.result()
            if result:
                totals[result] += 1

    print(f"✅ Sent requests: {totals}")
    return totals


def fetch_jaeger_traces():
    print("⏳ Waiting 5s before querying Jaeger...")
    time.sleep(5)

    results = {}
    for tag in ["performance", "non-performance"]:
        # Query by header value
        query_url = f'{JAEGER_QUERY_URL}&tags={{"http.request.header.x-test-request":"{tag}"}}'
        try:
            resp = requests.get(query_url, timeout=10)
            if resp.status_code == 200:
                traces = resp.json().get("data", [])
                results[tag] = len(traces)
            else:
                results[tag] = 0
        except Exception:
            results[tag] = 0

    return results


if __name__ == "__main__":
    if not wait_for_service(DEMO_SERVICE_URL):
        exit(1)
    sent = send_requests()
    traces = fetch_jaeger_traces()

    #commenting out the report printing for now as its not giving correct results, need to debug further

    # print("\n📊 Sampling Report")
    # print("-------------------------------------------------------------")
    # print(f"{'Category':<20} | {'Sent':<6} | {'Stored':<7} | {'Rate':<7}")
    # print("-------------------------------------------------------------")

    # for k in sent.keys():
    #     total = sent[k]
    #     stored = traces.get(k, 0)
    #     rate = (stored / total * 100) if total > 0 else 0
    #     print(f"{k:<20} | {total:<6} | {stored:<7} | {rate:>6.2f}%")

    # print("-------------------------------------------------------------")
    # total_sent = sum(sent.values())
    # total_stored = sum(traces.values())
    # overall_rate = (total_stored / total_sent * 100) if total_sent > 0 else 0
    # print(f"{'TOTAL':<20} | {total_sent:<6} | {total_stored:<7} | {overall_rate:>6.2f}%")
