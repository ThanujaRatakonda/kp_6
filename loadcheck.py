import requests
import concurrent.futures

URL = "http://10.131.103.92:5000/users"   # your backend service

def hit(_):
    try:
        r = requests.get(URL, timeout=2)
        return r.status_code
    except:
        return "ERR"

if __name__ == "__main__":
    n = int(input("Enter number of requests: "))

    print(f"\nSending {n} requests...\n")

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as exe:
        results = list(exe.map(hit, range(n)))

    print("Done.\nStatus codes:")
    print(results)


