from django.urls import path
from . import views, pdf_views, api_views

app_name = 'core'

urlpatterns = [
    path('api/add/', api_views.AlexaAddItemView.as_view(), name='alexa_add'),
    path('', views.HomeView.as_view(), name='home'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('list/create/', views.CreateBucketView.as_view(), name='list_create'),
    path('list/<uuid:pk>/', views.BucketListDetailView.as_view(), name='list_detail'),
    path('list/<uuid:pk>/calendar/', api_views.ICalExportView.as_view(), name='export_calendar'),
    path('list/<uuid:pk>/pdf/', pdf_views.ExportListPDFView.as_view(), name='export_pdf'),
    
    # Item CRUD
    path('list/<uuid:bucket_id>/add-form/', views.GetItemFormView.as_view(), name='get_add_form'),
    path('list/<uuid:bucket_id>/item/<int:item_id>/edit-form/', views.GetItemFormView.as_view(), name='get_edit_form'),
    
    path('list/<uuid:bucket_id>/add/', views.AddItemView.as_view(), name='add_item'),
    path('item/<int:item_id>/edit/', views.EditItemView.as_view(), name='edit_item'),
    path('item/<int:pk>/toggle/', views.ToggleItemView.as_view(), name='toggle_item'),
    path('item/<int:pk>/delete/', views.DeleteItemView.as_view(), name='delete_item'),
    path('list/<uuid:pk>/share-toggle/', views.ShareToggleView.as_view(), name='share_toggle'),
    path('settings/', views.ThemeSettingsView.as_view(), name='settings'),
]
