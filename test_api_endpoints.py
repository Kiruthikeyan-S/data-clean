import io
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"
    print("Health check endpoint OK")

def test_api_process_and_export():
    # 1. Upload CSV
    csv_bytes = b"Name,Email,Amount\nJohn Doe,john@test.com,$100\nJane Doe,jane@test.com,$200\n"
    res = client.post(
        "/api/process",
        files={"file": ("test.csv", csv_bytes, "text/csv")}
    )
    assert res.status_code == 200
    data = res.json()
    task_id = data["id"]
    assert data["status"] == "completed"
    assert data["classification"] == "structured"
    print(f"API /process OK, task_id: {task_id}")

    # 2. Test /api/result/{id}
    res_result = client.get(f"/api/result/{task_id}")
    assert res_result.status_code == 200
    assert res_result.json()["id"] == task_id
    print("API /result/{id} OK")

    # 3. Test /api/export/{id}/json
    res_exp_json = client.get(f"/api/export/{task_id}/json")
    assert res_exp_json.status_code == 200
    assert "application/json" in res_exp_json.headers["content-type"]
    print("API /export/json OK")

    # 4. Test /api/export/{id}/csv
    res_exp_csv = client.get(f"/api/export/{task_id}/csv")
    assert res_exp_csv.status_code == 200
    assert "text/csv" in res_exp_csv.headers["content-type"]
    print("API /export/csv OK")

    # 5. Test /api/export/{id}/excel
    res_exp_excel = client.get(f"/api/export/{task_id}/excel")
    assert res_exp_excel.status_code == 200
    assert "spreadsheetml" in res_exp_excel.headers["content-type"]
    print("API /export/excel OK")

if __name__ == "__main__":
    test_api_health()
    test_api_process_and_export()
    print("\nALL API ENDPOINTS TESTED AND VERIFIED SUCCESSFULLY!")
