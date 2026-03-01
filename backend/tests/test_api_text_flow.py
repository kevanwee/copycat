from __future__ import annotations



def test_text_case_api_flow(client):
    create_resp = client.post("/api/v1/cases", json={"jurisdiction": "SG", "metadata": {}})
    assert create_resp.status_code == 200
    case_id = create_resp.json()["case_id"]

    files = {"file": ("original.txt", b"hello singapore copyright law text", "text/plain")}
    data = {"role": "original", "media_type": "text"}
    up1 = client.post(f"/api/v1/cases/{case_id}/artifacts", files=files, data=data)
    assert up1.status_code == 200

    files2 = {"file": ("alleged.txt", b"hello singapore copyright law text", "text/plain")}
    data2 = {"role": "alleged", "media_type": "text"}
    up2 = client.post(f"/api/v1/cases/{case_id}/artifacts", files=files2, data=data2)
    assert up2.status_code == 200

    analyze = client.post(f"/api/v1/cases/{case_id}/analyze")
    assert analyze.status_code == 200
    job_id = analyze.json()["job_id"]

    job = client.get(f"/api/v1/jobs/{job_id}")
    assert job.status_code == 200

    report = client.get(f"/api/v1/cases/{case_id}/report")
    assert report.status_code == 200
    body = report.json()["report"]
    assert body["headline_overlap_percentage"] >= 99.0
    assert body["rule_pack_version"] == "sg_v1"