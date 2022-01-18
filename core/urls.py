from django.urls import path
from django.contrib import admin

import app.views

admin.autodiscover()


urlpatterns = [
    path('', app.views.index, name='index'),
    path('db/', app.views.db, name='db'),
    path('emissions/', app.views.emissions, name='emissions'),
    path('emissions/<int:page>', app.views.emissions, name='emissions'),
    path('emissions/imo/', app.views.emission_detail, name='emission_detail'),
    path('emissions/imo/<int:imo>', app.views.emission_detail, name='emission_detail'),
    path('aggregation/', app.views.aggregation, name='aggregation'),
    path('aggregation/<int:page>', app.views.aggregation, name='aggregation'),
    path('visual/', app.views.visual_view, name='visual'),
    path('fuel_performance/', app.views.extended_view, name='extended_view'),
    path('verifiers_ranking/', app.views.extended_view_graph2, name='extended_view_graph2'),
    path('built_year_efficiency/', app.views.extended_view_graph3, name='extended_view_graph3'),
    path('admin/', admin.site.urls)
]
