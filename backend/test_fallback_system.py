import requests
import time

BASE_URL = "http://127.0.0.1:8000/api"
REPO_URL = "https://github.com/tiangolo/fastapi"


def print_section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


# -------------------------------------------------------
# STEP 1 — UPLOAD (FIXED)
# -------------------------------------------------------
def upload():
    print_section("STEP 1 — UPLOAD")

    res = requests.post(
        f"{BASE_URL}/upload",
        data={"github_url": REPO_URL}   # ✅ CORRECT FIELD
    )

    try:
        data = res.json()
    except:
        print("❌ Non-JSON response:", res.text)
        return None

    if res.status_code != 200:
        print(f"❌ Upload failed ({res.status_code}):", data)
        return None

    project_id = data["project_id"]
    print(f"✅ Project ID: {project_id}")
    return project_id


# -------------------------------------------------------
# STEP 2 — PIPELINE
# -------------------------------------------------------
def wait_pipeline(project_id):
    print_section("STEP 2 — PIPELINE")

    for _ in range(60):
        res = requests.get(f"{BASE_URL}/status/{project_id}")
        data = res.json()

        percent = data.get("percent", 0)
        step = data.get("current_step_name", "")

        print(f"[{percent}%] {step}")

        if percent == 100:
            print("✅ Pipeline complete")
            return True

        time.sleep(2)

    print("❌ Timeout")
    return False


# -------------------------------------------------------
# STEP 3 — ANALYSIS
# -------------------------------------------------------
def test_analysis(project_id):
    print_section("STEP 3 — ANALYSIS")

    res = requests.get(f"{BASE_URL}/analysis/{project_id}")
    data = res.json()

    print("Type:", data.get("type"))
    print("Tech stack:", data.get("tech_stack"))
    print("Score:", data.get("security_score"))
    print("Issues:", len(data.get("issues", [])))


# -------------------------------------------------------
# STEP 4 — CHAT
# -------------------------------------------------------
def test_chat(project_id):
    print_section("STEP 4 — CHAT (FALLBACK)")

    questions = [
        "Where is authentication handled?",
        "Which file defines API routes?",
        "What is main entry point?",
    ]

    for q in questions:
        res = requests.post(
            f"{BASE_URL}/chat",
            json={
                "project_id": project_id,
                "question": q,
                "role": "dev"
            }
        )

        data = res.json()

        print("\nQ:", q)
        print("Mode:", data.get("mode"))
        print("Confidence:", data.get("confidence"))
        print("Sources:", data.get("sources"))
        print("Answer:", data.get("answer")[:150], "...")


# -------------------------------------------------------
# STEP 5 — WORKFLOW
# -------------------------------------------------------
def test_workflow(project_id):
    print_section("STEP 5 — WORKFLOW")

    print(requests.get(f"{BASE_URL}/workflow/{project_id}").json())

    print("\nDEV:")
    print(requests.get(f"{BASE_URL}/workflow/{project_id}/view/dev").json())

    print("\nPM:")
    print(requests.get(f"{BASE_URL}/workflow/{project_id}/view/pm").json())

    print("\nINVESTOR:")
    print(requests.get(f"{BASE_URL}/workflow/{project_id}/view/investor").json())


# -------------------------------------------------------
# STEP 6 — MOCK
# -------------------------------------------------------
def test_mock(project_id):
    print_section("STEP 6 — MOCK")

    res = requests.get(f"{BASE_URL}/mock/{project_id}")
    data = res.json()

    print("Mock emails:", data.get("mock_emails"))
    print("Users:", len(data.get("sample_users", [])))


# -------------------------------------------------------
# MAIN
# -------------------------------------------------------
def main():
    print("\n🚨 FALLBACK TEST START")

    project_id = upload()
    if not project_id:
        return

    if not wait_pipeline(project_id):
        return

    test_analysis(project_id)
    test_chat(project_id)
    test_workflow(project_id)
    test_mock(project_id)

    print("\n🎯 DONE")


if __name__ == "__main__":
    main()