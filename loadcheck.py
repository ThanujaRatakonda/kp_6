import requests
import concurrent.futures
import time

# URL via your ingress
URL = "http://backend.local/users"  # make sure backend.local resolves to your cluster

def hit(i):
    try:
        r = requests.get(URL, timeout=5)
        pod = r.headers.get("X-Pod-Name", "unknown-pod")
        elapsed = r.elapsed.total_seconds()
        return i, pod, elapsed
    except Exception:
        return i, "ERR-POD", None

def main():
    total = int(input("Number of requests: "))
    start_time = time.time()
    results = []

    # ThreadPoolExecutor for concurrency
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(hit, i+1) for i in range(total)]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    # Count requests per pod
    pod_count = {}
    for i, pod, elapsed in results:
        print(f"Request {i}: served by {pod} (time: {elapsed}s)")
        pod_count[pod] = pod_count.get(pod, 0) + 1

    print("\n--- ACTUAL POD HIT COUNT ---")
    for pod, count in pod_count.items():
        print(f"{pod}: {count} requests")

    print(f"\nTotal time: {time.time() - start_time:.3f}s")

if __name__ == "__main__":
    main()
