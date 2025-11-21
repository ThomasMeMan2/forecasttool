"""
Comprehensive Test Suite for Forecast Studio
Tests all 4 phases with demo data
"""
import pytest
import requests
import json
import time
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
DEMO_DATA_PATH = Path(__file__).parent.parent / "demo_data"

# Test users
TEST_USERS = [
    {
        "email": "test_user_1@example.com",
        "password": "TestPass123!",
        "full_name": "Test User One",
        "organization": "Test Org"
    },
    {
        "email": "test_user_2@example.com",
        "password": "TestPass123!",
        "full_name": "Test User Two",
        "organization": "Test Org"
    }
]


class TestResults:
    """Track test results"""
    def __init__(self):
        self.passed = []
        self.failed = []
        self.skipped = []

    def add_pass(self, test_name):
        self.passed.append(test_name)
        print(f"✓ {test_name}")

    def add_fail(self, test_name, error):
        self.failed.append((test_name, error))
        print(f"✗ {test_name}: {error}")

    def add_skip(self, test_name, reason):
        self.skipped.append((test_name, reason))
        print(f"⊘ {test_name}: {reason}")

    def print_summary(self):
        total = len(self.passed) + len(self.failed) + len(self.skipped)
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {total}")
        print(f"✓ Passed: {len(self.passed)} ({len(self.passed)/total*100:.1f}%)")
        print(f"✗ Failed: {len(self.failed)} ({len(self.failed)/total*100:.1f}%)")
        print(f"⊘ Skipped: {len(self.skipped)} ({len(self.skipped)/total*100:.1f}%)")

        if self.failed:
            print(f"\nFailed Tests:")
            for test_name, error in self.failed:
                print(f"  - {test_name}: {error}")


results = TestResults()


def api_call(method, endpoint, **kwargs):
    """Make API call with error handling"""
    url = f"{BASE_URL}{endpoint}"
    try:
        response = requests.request(method, url, **kwargs)
        return response
    except requests.exceptions.ConnectionError:
        raise Exception(f"Cannot connect to API at {BASE_URL}. Is the server running?")


# ====================== AUTHENTICATION TESTS ======================

def test_auth_001_register_user():
    """TEST_AUTH_001: Register new user with valid data"""
    try:
        response = api_call("POST", "/api/auth/register", json=TEST_USERS[0])
        if response.status_code in [201, 400]:  # 400 if already exists
            if response.status_code == 400 and "already registered" in response.json().get("detail", "").lower():
                results.add_pass("TEST_AUTH_001 (user already exists)")
            elif response.status_code == 201:
                results.add_pass("TEST_AUTH_001")
            else:
                results.add_fail("TEST_AUTH_001", f"Unexpected response: {response.status_code}")
        else:
            results.add_fail("TEST_AUTH_001", f"Status: {response.status_code}, Body: {response.text}")
    except Exception as e:
        results.add_fail("TEST_AUTH_001", str(e))


def test_auth_002_duplicate_email():
    """TEST_AUTH_002: Register with duplicate email (should fail)"""
    try:
        # Try to register same user again
        response = api_call("POST", "/api/auth/register", json=TEST_USERS[0])
        if response.status_code == 400:
            results.add_pass("TEST_AUTH_002")
        else:
            results.add_fail("TEST_AUTH_002", f"Expected 400, got {response.status_code}")
    except Exception as e:
        results.add_fail("TEST_AUTH_002", str(e))


def test_auth_005_login_valid():
    """TEST_AUTH_005: Login with valid credentials"""
    try:
        response = api_call("POST", "/api/auth/token", data={
            "username": TEST_USERS[0]["email"],
            "password": TEST_USERS[0]["password"]
        })
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data and "token_type" in data:
                # Store token for later tests
                global USER1_TOKEN
                USER1_TOKEN = data["access_token"]
                results.add_pass("TEST_AUTH_005")
            else:
                results.add_fail("TEST_AUTH_005", "Missing token fields in response")
        else:
            results.add_fail("TEST_AUTH_005", f"Status: {response.status_code}")
    except Exception as e:
        results.add_fail("TEST_AUTH_005", str(e))


def test_auth_006_login_invalid_password():
    """TEST_AUTH_006: Login with invalid password (should fail)"""
    try:
        response = api_call("POST", "/api/auth/token", data={
            "username": TEST_USERS[0]["email"],
            "password": "WrongPassword!"
        })
        if response.status_code == 401:
            results.add_pass("TEST_AUTH_006")
        else:
            results.add_fail("TEST_AUTH_006", f"Expected 401, got {response.status_code}")
    except Exception as e:
        results.add_fail("TEST_AUTH_006", str(e))


def test_auth_009_protected_without_token():
    """TEST_AUTH_009: Access protected endpoint without token (should fail 401)"""
    try:
        response = api_call("GET", "/api/auth/me")
        if response.status_code == 401:
            results.add_pass("TEST_AUTH_009")
        else:
            results.add_fail("TEST_AUTH_009", f"Expected 401, got {response.status_code}")
    except Exception as e:
        results.add_fail("TEST_AUTH_009", str(e))


def test_auth_011_protected_with_token():
    """TEST_AUTH_011: Access protected endpoint with valid token (should succeed)"""
    try:
        if 'USER1_TOKEN' not in globals():
            results.add_skip("TEST_AUTH_011", "No token available (login failed)")
            return

        response = api_call("GET", "/api/auth/me", headers={
            "Authorization": f"Bearer {USER1_TOKEN}"
        })
        if response.status_code == 200:
            data = response.json()
            if data["email"] == TEST_USERS[0]["email"]:
                results.add_pass("TEST_AUTH_011")
            else:
                results.add_fail("TEST_AUTH_011", "Wrong user returned")
        else:
            results.add_fail("TEST_AUTH_011", f"Status: {response.status_code}")
    except Exception as e:
        results.add_fail("TEST_AUTH_011", str(e))


# ====================== PROJECT TESTS ======================

def test_proj_001_create_project():
    """TEST_PROJ_001: Create new project"""
    try:
        if 'USER1_TOKEN' not in globals():
            results.add_skip("TEST_PROJ_001", "No token available")
            return

        response = api_call("POST", "/api/projects",
            headers={"Authorization": f"Bearer {USER1_TOKEN}"},
            json={
                "name": "Demo Retail Project",
                "description": "Test project with demo data"
            }
        )
        if response.status_code == 201:
            data = response.json()
            global PROJECT_ID
            PROJECT_ID = data["id"]
            results.add_pass("TEST_PROJ_001")
        else:
            results.add_fail("TEST_PROJ_001", f"Status: {response.status_code}, Body: {response.text}")
    except Exception as e:
        results.add_fail("TEST_PROJ_001", str(e))


def test_proj_002_list_projects():
    """TEST_PROJ_002: List all projects for user"""
    try:
        if 'USER1_TOKEN' not in globals():
            results.add_skip("TEST_PROJ_002", "No token available")
            return

        response = api_call("GET", "/api/projects",
            headers={"Authorization": f"Bearer {USER1_TOKEN}"}
        )
        if response.status_code == 200:
            projects = response.json()
            if isinstance(projects, list) and len(projects) > 0:
                results.add_pass("TEST_PROJ_002")
            else:
                results.add_fail("TEST_PROJ_002", "No projects returned")
        else:
            results.add_fail("TEST_PROJ_002", f"Status: {response.status_code}")
    except Exception as e:
        results.add_fail("TEST_PROJ_002", str(e))


# ====================== DATA UPLOAD TESTS ======================

def test_data_002_upload_demo_data():
    """TEST_DATA_002: Upload demo_timeseries_data.csv successfully"""
    try:
        if 'PROJECT_ID' not in globals():
            results.add_skip("TEST_DATA_002", "No project created")
            return

        csv_path = DEMO_DATA_PATH / "demo_timeseries_data.csv"
        if not csv_path.exists():
            results.add_skip("TEST_DATA_002", "Demo data file not found")
            return

        with open(csv_path, 'rb') as f:
            response = api_call("POST", f"/api/datasets/{PROJECT_ID}/upload",
                headers={"Authorization": f"Bearer {USER1_TOKEN}"},
                files={"file": ("demo_data.csv", f, "text/csv")}
            )

        if response.status_code in [201, 200]:
            global DATASET_ID
            data = response.json()
            DATASET_ID = data.get("id")
            results.add_pass("TEST_DATA_002")
        else:
            results.add_fail("TEST_DATA_002", f"Status: {response.status_code}, Body: {response.text}")
    except Exception as e:
        results.add_fail("TEST_DATA_002", str(e))


def test_data_007_timeseries_extracted():
    """TEST_DATA_007: Time series are extracted correctly (6 series from demo data)"""
    try:
        if 'PROJECT_ID' not in globals():
            results.add_skip("TEST_DATA_007", "No project created")
            return

        response = api_call("GET", f"/api/datasets/{PROJECT_ID}/timeseries",
            headers={"Authorization": f"Bearer {USER1_TOKEN}"}
        )

        if response.status_code == 200:
            timeseries = response.json()
            if len(timeseries) == 6:
                ts_ids = [ts["ts_id"] for ts in timeseries]
                expected = ["PRODUCT_A", "PRODUCT_B", "PRODUCT_C", "STORE_001", "STORE_002", "REGION_NORTH"]
                if all(id in ts_ids for id in expected):
                    results.add_pass("TEST_DATA_007")
                else:
                    results.add_fail("TEST_DATA_007", f"Missing expected time series. Got: {ts_ids}")
            else:
                results.add_fail("TEST_DATA_007", f"Expected 6 time series, got {len(timeseries)}")
        else:
            results.add_fail("TEST_DATA_007", f"Status: {response.status_code}")
    except Exception as e:
        results.add_fail("TEST_DATA_007", str(e))


# ====================== FORECASTING TESTS ======================

def test_fcst_001_generate_forecast():
    """TEST_FCST_001: Generate forecast for single time series"""
    try:
        if 'PROJECT_ID' not in globals():
            results.add_skip("TEST_FCST_001", "No project created")
            return

        response = api_call("POST", f"/api/forecasts/{PROJECT_ID}/generate",
            headers={"Authorization": f"Bearer {USER1_TOKEN}"},
            json={
                "timeseries_ids": ["PRODUCT_A"],
                "horizon": 12,
                "confidence_level": 90
            }
        )

        if response.status_code == 201:
            forecasts = response.json()
            if len(forecasts) > 0:
                forecast = forecasts[0]
                global FORECAST_ID
                FORECAST_ID = forecast["id"]
                # Check forecast structure
                if "forecast_data" in forecast and len(forecast["forecast_data"]) == 12:
                    results.add_pass("TEST_FCST_001")
                else:
                    results.add_fail("TEST_FCST_001", "Invalid forecast structure")
            else:
                results.add_fail("TEST_FCST_001", "No forecasts returned")
        else:
            results.add_fail("TEST_FCST_001", f"Status: {response.status_code}, Body: {response.text}")
    except Exception as e:
        results.add_fail("TEST_FCST_001", str(e))


def test_fcst_005_forecast_structure():
    """TEST_FCST_005: Forecast data structure is correct (mean, lower, upper bounds)"""
    try:
        if 'FORECAST_ID' not in globals():
            results.add_skip("TEST_FCST_005", "No forecast created")
            return

        response = api_call("GET", f"/api/forecasts/{PROJECT_ID}/forecasts/{FORECAST_ID}",
            headers={"Authorization": f"Bearer {USER1_TOKEN}"}
        )

        if response.status_code == 200:
            forecast = response.json()
            if "forecast_data" in forecast:
                point = forecast["forecast_data"][0]
                required_fields = ["timestamp", "mean", "lower_80", "upper_80", "lower_90", "upper_90"]
                if all(field in point for field in required_fields):
                    results.add_pass("TEST_FCST_005")
                else:
                    results.add_fail("TEST_FCST_005", f"Missing required fields. Got: {point.keys()}")
            else:
                results.add_fail("TEST_FCST_005", "No forecast_data in response")
        else:
            results.add_fail("TEST_FCST_005", f"Status: {response.status_code}")
    except Exception as e:
        results.add_fail("TEST_FCST_005", str(e))


# ====================== EVENTS TESTS ======================

def test_evnt_001_create_global_event():
    """TEST_EVNT_001: Create global event"""
    try:
        if 'PROJECT_ID' not in globals():
            results.add_skip("TEST_EVNT_001", "No project created")
            return

        response = api_call("POST", f"/api/events/{PROJECT_ID}/global-events",
            headers={"Authorization": f"Bearer {USER1_TOKEN}"},
            json={
                "event_name": "Test Holiday",
                "event_date": "2024-01-01",
                "event_type": "holiday",
                "description": "Test event"
            }
        )

        if response.status_code == 201:
            results.add_pass("TEST_EVNT_001")
        else:
            results.add_fail("TEST_EVNT_001", f"Status: {response.status_code}, Body: {response.text}")
    except Exception as e:
        results.add_fail("TEST_EVNT_001", str(e))


# ====================== DIAGNOSTICS TESTS ======================

def test_diag_001_generate_diagnostics():
    """TEST_DIAG_001: Generate full diagnostics for time series"""
    try:
        if 'PROJECT_ID' not in globals():
            results.add_skip("TEST_DIAG_001", "No project created")
            return

        response = api_call("GET", f"/api/diagnostics/{PROJECT_ID}/timeseries/PRODUCT_A/diagnostics",
            headers={"Authorization": f"Bearer {USER1_TOKEN}"},
            params={"frequency": "D"}
        )

        if response.status_code == 200:
            data = response.json()
            if "diagnostics" in data:
                diag = data["diagnostics"]
                required = ["acf_results", "pacf_results", "stationarity", "summary_stats"]
                if all(key in diag for key in required):
                    results.add_pass("TEST_DIAG_001")
                else:
                    results.add_fail("TEST_DIAG_001", f"Missing diagnostic components. Got: {diag.keys()}")
            else:
                results.add_fail("TEST_DIAG_001", "No diagnostics in response")
        else:
            results.add_fail("TEST_DIAG_001", f"Status: {response.status_code}, Body: {response.text}")
    except Exception as e:
        results.add_fail("TEST_DIAG_001", str(e))


# ====================== INSIGHTS TESTS ======================

def test_insg_001_generate_history_insight():
    """TEST_INSG_001: Generate history summary insight"""
    try:
        if 'PROJECT_ID' not in globals():
            results.add_skip("TEST_INSG_001", "No project created")
            return

        response = api_call("POST", f"/api/insights/{PROJECT_ID}/timeseries/PRODUCT_A/insights/history",
            headers={"Authorization": f"Bearer {USER1_TOKEN}"}
        )

        if response.status_code == 200:
            data = response.json()
            if "insight" in data and "text" in data["insight"]:
                results.add_pass("TEST_INSG_001")
            else:
                results.add_fail("TEST_INSG_001", "Invalid insight structure")
        else:
            results.add_fail("TEST_INSG_001", f"Status: {response.status_code}, Body: {response.text}")
    except Exception as e:
        results.add_fail("TEST_INSG_001", str(e))


# ====================== SHARING TESTS ======================

def test_shre_001_share_project():
    """TEST_SHRE_001: Owner shares project with another user"""
    try:
        # First, register second user
        response = api_call("POST", "/api/auth/register", json=TEST_USERS[1])
        # Ignore if already exists

        # Login as second user to get token
        response = api_call("POST", "/api/auth/token", data={
            "username": TEST_USERS[1]["email"],
            "password": TEST_USERS[1]["password"]
        })
        if response.status_code == 200:
            global USER2_TOKEN
            USER2_TOKEN = response.json()["access_token"]

        if 'PROJECT_ID' not in globals() or 'USER1_TOKEN' not in globals():
            results.add_skip("TEST_SHRE_001", "Prerequisites not met")
            return

        # Share project from user 1 to user 2
        response = api_call("POST", f"/api/sharing/{PROJECT_ID}/shares",
            headers={"Authorization": f"Bearer {USER1_TOKEN}"},
            json={
                "email": TEST_USERS[1]["email"],
                "can_view": True,
                "can_edit": False,
                "can_delete": False,
                "can_share": False
            }
        )

        if response.status_code == 201:
            results.add_pass("TEST_SHRE_001")
        elif response.status_code == 400 and "already shared" in response.json().get("detail", "").lower():
            results.add_pass("TEST_SHRE_001 (already shared)")
        else:
            results.add_fail("TEST_SHRE_001", f"Status: {response.status_code}, Body: {response.text}")
    except Exception as e:
        results.add_fail("TEST_SHRE_001", str(e))


# ====================== COMPARISON TESTS ======================

def test_comp_001_create_comparison():
    """TEST_COMP_001: Create comparison with 2 forecasts"""
    try:
        if 'PROJECT_ID' not in globals() or 'FORECAST_ID' not in globals():
            results.add_skip("TEST_COMP_001", "No forecasts available")
            return

        # Generate a second forecast first
        response = api_call("POST", f"/api/forecasts/{PROJECT_ID}/generate",
            headers={"Authorization": f"Bearer {USER1_TOKEN}"},
            json={
                "timeseries_ids": ["PRODUCT_B"],
                "horizon": 12,
                "confidence_level": 90
            }
        )

        if response.status_code == 201:
            forecast2_id = response.json()[0]["id"]

            # Create comparison
            response = api_call("POST", f"/api/comparison/{PROJECT_ID}/comparisons",
                headers={"Authorization": f"Bearer {USER1_TOKEN}"},
                json={
                    "comparison_name": "Test Comparison",
                    "forecast_ids": [FORECAST_ID, forecast2_id]
                }
            )

            if response.status_code == 201:
                data = response.json()
                if "comparison_metrics" in data:
                    results.add_pass("TEST_COMP_001")
                else:
                    results.add_fail("TEST_COMP_001", "Missing comparison_metrics")
            else:
                results.add_fail("TEST_COMP_001", f"Status: {response.status_code}")
        else:
            results.add_fail("TEST_COMP_001", "Failed to create second forecast")
    except Exception as e:
        results.add_fail("TEST_COMP_001", str(e))


# ====================== MAIN TEST RUNNER ======================

def run_all_tests():
    """Run all tests in order"""
    print("="*60)
    print("FORECAST STUDIO - COMPREHENSIVE TEST SUITE")
    print("="*60)
    print(f"\nAPI Base URL: {BASE_URL}")
    print(f"Demo Data Path: {DEMO_DATA_PATH}")
    print()

    # Check if server is running
    try:
        api_call("GET", "/api/health")
        print("✓ API server is running\n")
    except Exception as e:
        print(f"✗ Cannot connect to API server: {e}")
        print("Please start the server with: docker-compose up")
        return

    print("Running tests...\n")
    print("=" * 60)
    print("AUTHENTICATION TESTS")
    print("=" * 60)
    test_auth_001_register_user()
    test_auth_002_duplicate_email()
    test_auth_005_login_valid()
    test_auth_006_login_invalid_password()
    test_auth_009_protected_without_token()
    test_auth_011_protected_with_token()

    print("\n" + "=" * 60)
    print("PROJECT TESTS")
    print("=" * 60)
    test_proj_001_create_project()
    test_proj_002_list_projects()

    print("\n" + "=" * 60)
    print("DATA UPLOAD TESTS")
    print("=" * 60)
    test_data_002_upload_demo_data()
    test_data_007_timeseries_extracted()

    print("\n" + "=" * 60)
    print("FORECASTING TESTS")
    print("=" * 60)
    test_fcst_001_generate_forecast()
    test_fcst_005_forecast_structure()

    print("\n" + "=" * 60)
    print("EVENTS TESTS")
    print("=" * 60)
    test_evnt_001_create_global_event()

    print("\n" + "=" * 60)
    print("DIAGNOSTICS TESTS")
    print("=" * 60)
    test_diag_001_generate_diagnostics()

    print("\n" + "=" * 60)
    print("INSIGHTS TESTS")
    print("=" * 60)
    test_insg_001_generate_history_insight()

    print("\n" + "=" * 60)
    print("SHARING TESTS")
    print("=" * 60)
    test_shre_001_share_project()

    print("\n" + "=" * 60)
    print("COMPARISON TESTS")
    print("=" * 60)
    test_comp_001_create_comparison()

    # Print summary
    results.print_summary()

    # Return exit code
    return 0 if len(results.failed) == 0 else 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    exit(exit_code)
