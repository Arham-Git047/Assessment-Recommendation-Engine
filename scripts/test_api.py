import urllib.request, json

req = urllib.request.Request(
    "http://127.0.0.1:8000/recommend",
    data=json.dumps({"query": "Java developer backend engineering", "top_k": 5}).encode(),
    headers={"Content-Type": "application/json"},
)
r = urllib.request.urlopen(req)
data = json.loads(r.read())
print(f"Got {len(data['recommended_assessments'])} results\n")
for a in data["recommended_assessments"]:
    print(f"  {a['assessment_name']}")
    print(f"    URL: {a['url']}")
    print(f"    Type: {a['test_type']} | Duration: {a['duration']}min | Remote: {a['remote_support']} | Adaptive: {a['adaptive_support']}")
    print()
