def test_generate_unofficial_task(logged_in):
    resp = logged_in.post("/generate_unofficial/", data={"tier": "easy"})
    assert resp.status_code == 200, resp.data[:300]


def test_official_user_can_generate_task(client, make_user, login):
    make_user(username="off", official=True)
    login(username="off")
    resp = client.post("/generate/")
    assert resp.status_code == 200, resp.data[:300]
    assert resp.get_json()["name"]
