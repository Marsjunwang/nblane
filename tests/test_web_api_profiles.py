"""Profile onboarding uses the real HTTP auth and agent policies."""

from __future__ import annotations

from fastapi.testclient import TestClient

from test_web_api_accounts import AccountsTestBase


class TestProfileInitialization(AccountsTestBase):
    def test_admin_creates_private_profile_and_first_plan(self) -> None:
        client = self.login()
        response = client.post("/api/v1/profiles", json={
            "name": "new-profile", "schema": "robotics-engineer",
            "north_star": "Build useful robots", "goal_title": "Deliver a prototype",
            "task_title": "Define acceptance criteria",
        })
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json(), {"name": "new-profile", "has_first_plan": True})
        listed = client.get("/api/v1/profiles")
        self.assertIn("new-profile", [row["name"] for row in listed.json()])
        duplicate = client.post("/api/v1/profiles", json={
            "name": "new-profile", "schema": "autonomous-driving",
        })
        self.assertEqual((duplicate.status_code, duplicate.json()["code"]), (409, "profile_exists"))

    def test_only_human_admin_can_create(self) -> None:
        body = {"name": "denied", "schema": "robotics-engineer"}
        self.assertEqual(TestClient(self.app).post("/api/v1/profiles", json=body).status_code, 401)
        self.assertEqual(self.login("wang").post("/api/v1/profiles", json=body).status_code, 403)
        response = self.login("bot").post("/api/v1/profiles", json=body)
        self.assertEqual(response.status_code, 403, response.text)
        self.assertFalse((self.profiles / "denied").exists())

    def test_invalid_input_is_rejected_without_files(self) -> None:
        client = self.login()
        for extra in ({"schema": "../escape"}, {"task_title": "No goal"}, {"name": "../escape"}):
            body = {"name": "invalid", "schema": "robotics-engineer", **extra}
            response = client.post("/api/v1/profiles", json=body)
            self.assertEqual(response.status_code, 422, response.text)
        self.assertFalse((self.profiles / "invalid").exists())
