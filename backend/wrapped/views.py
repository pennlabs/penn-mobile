from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.db import transaction
from wrapped.models import Page, IndividualStat, GlobalStat
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from rest_framework import generics, viewsets
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .serializers import PageSerializer

User = get_user_model()


class GeneratePage(viewsets.ModelViewSet): 
    queryset = User.objects.all()

    @action(detail=False, methods=["get"])
    def user_generation(self, request):  
        username = request.GET.get('username')    
        semester = request.GET.get("semester")
        if not username:
            return Response({"error": "Username parameter is required"}, status=400)

        # Find the user
        user = get_object_or_404(User, username=username)

        # Filter pages by this user
        # pages = Page.objects.filter(user=user)
        pages = Page.objects.filter(semester=semester)

        # Serialize the data
        serializer = PageSerializer(pages, many=True)
        return Response(serializer.data, status=200)