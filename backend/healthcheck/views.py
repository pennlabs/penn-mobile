import time

import requests
from django.conf import settings
from django.utils import timezone
from requests.auth import HTTPBasicAuth
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from laundry.api_wrapper import check_is_working


class FeatureHealth(APIView):
    """
    GET: Unauthenticated endpoint for healthchecks.
    Polled by status.pennlabs.org.
    """

    def _check(self, name, check_fn):
        start = time.time()
        try:
            check_fn()
            return {"status": "ok", "response_time_ms": round((time.time() - start) * 1000)}
        except Exception as e:
            return {
                "status": "error",
                "response_time_ms": round((time.time() - start) * 1000),
                "error": str(e),
            }

    def _check_laundry(self):
        if not check_is_working():
            raise Exception("Laundry API is not responding")

    def _check_dining(self):
        from dining.api_wrapper import DiningAPIWrapper

        d = DiningAPIWrapper()
        d.update_token()
        response = d.request(
            "GET", "https://3scale-public-prod-open-data.apps.k8s.upenn.edu/api/v1/dining/venues"
        )
        if response.status_code != 200:
            raise Exception(f"Dining API returned {response.status_code}")

    def _check_wharton_gsr(self):
        response = requests.get(
            "https://apps.wharton.upenn.edu/gsr/api/v1/privileges",
            headers={"Authorization": f"Token {settings.WHARTON_TOKEN}"},
            timeout=10,
        )
        if response.status_code not in (200, 403, 404):
            raise Exception(f"Wharton API returned {response.status_code}")

    def _check_libcal_gsr(self):
        body = {
            "client_id": settings.GENERAL_LIBCAL_ID,
            "client_secret": settings.GENERAL_LIBCAL_SECRET,
            "grant_type": "client_credentials",
        }
        response = requests.post("https://api2.libcal.com/1.1/oauth/token", data=body, timeout=10)
        if response.status_code != 200:
            raise Exception(f"LibCal token endpoint returned {response.status_code}")

    def _check_penngroups_gsr(self):
        response = requests.get(
            "https://grouperWs.apps.upenn.edu/grouperWs/servicesRest/4.9.3/subjects",
            auth=HTTPBasicAuth(settings.PENNGROUPS_USERNAME, settings.PENNGROUPS_PASSWORD),
            timeout=10,
        )
        if response.status_code >= 500:
            raise Exception(f"PennGroups API returned {response.status_code}")

    def get(self, request):
        features = {
            "laundry": self._check("laundry", self._check_laundry),
            "dining": self._check("dining", self._check_dining),
            "wharton_gsr": self._check("wharton_gsr", self._check_wharton_gsr),
            "libcal_gsr": self._check("libcal_gsr", self._check_libcal_gsr),
            "penngroups_gsr": self._check("penngroups_gsr", self._check_penngroups_gsr),
        }
        all_ok = all(f["status"] == "ok" for f in features.values())
        return Response(
            {
                "status": "ok" if all_ok else "degraded",
                "features": features,
                "timestamp": timezone.now().isoformat(),
            },
            status=status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE,
        )
