import requests
import concurrent.futures

URL = "http://localhost:5000/users"

def hit(i):
    try:
        r = requests.get(URL, timeout=5)
        return i, r.headers.get("X-Pod-Name", "unknown-pod")
    except:
        return i, "ERR-POD"

def main():
    total = int(input("Number of requests: "))
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
        futures = [ex.submit(hit, i+1) for i in range(total)]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    pods = {}
    for i, pod in results:
        print(f"Request {i}: served by {pod}")
        pods[pod] = pods.get(pod, 0) + 1

    print("\n--- POD HIT COUNT ---")
    for pod, count in pods.items():
        print(f"{pod}: {count} requests")

if __name__ == "__main__":
    main()
