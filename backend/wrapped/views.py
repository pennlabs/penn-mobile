from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from wrapped.models import Semester
from wrapped.serializers import SemesterSerializer


class SemesterView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, semester_id):
        semester = Semester.objects.get(semester=semester_id)
        serializer = SemesterSerializer(semester, context={"user": request.user})
        return Response(serializer.data)
