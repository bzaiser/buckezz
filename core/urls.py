from django.urls import path
from django.contrib.auth import views as auth_views
from . import views, pdf_views, api_views

app_name = 'core'

urlpatterns = [
    # Auth
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='core:home'), name='logout'),
    
    path('api/add/', api_views.AlexaAddItemView.as_view(), name='alexa_add'),
    path('api/alexa-skill/', api_views.AlexaSkillView.as_view(), name='alexa_skill'),
    path('api/alexa-skill', api_views.AlexaSkillView.as_view(), name='alexa_skill_no_slash'),
    path('api/alexa-log/', api_views.AlexaLogView.as_view(), name='alexa_log'),
    path('api/person/add/', api_views.QuickAddPersonView.as_view(), name='quick_add_person'),
    path('', views.HomeView.as_view(), name='home'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('list/create/', views.CreateBucketView.as_view(), name='list_create'),
    path('list/<uuid:pk>/', views.BucketListDetailView.as_view(), name='list_detail'),
    path('list/<uuid:pk>/calendar/', api_views.ICalExportView.as_view(), name='export_calendar'),
    path('list/<uuid:pk>/pdf/', pdf_views.ExportListPDFView.as_view(), name='export_pdf'),
    path('list/<uuid:pk>/pdf/raw/export.pdf', pdf_views.ExportListRawPDFView.as_view(), name='export_pdf_raw'),
    
    # Item CRUD
    path('list/<uuid:bucket_id>/add-form/', views.GetItemFormView.as_view(), name='get_add_form'),
    path('list/<uuid:bucket_id>/item/<int:item_id>/edit-form/', views.GetItemFormView.as_view(), name='get_edit_form'),
    
    path('list/<uuid:bucket_id>/add/', views.AddItemView.as_view(), name='add_item'),
    path('item/<int:item_id>/edit/', views.EditItemView.as_view(), name='edit_item'),
    path('item/<int:pk>/toggle/', views.ToggleItemView.as_view(), name='toggle_item'),
    path('item/<int:pk>/delete/', views.DeleteItemView.as_view(), name='delete_item'),
    path('list/<uuid:bucket_id>/reorder/', views.ReorderItemsView.as_view(), name='reorder_items'),
    path('role/<int:role_id>/cycle/', views.CyclePersonRoleView.as_view(), name='cycle_person_role'),
    path('item/<int:item_id>/reserve/', views.ToggleReservationView.as_view(), name='toggle_reservation'),
    path('item/<int:item_id>/toggle-tracker/', views.ToggleTrackerLogView.as_view(), name='toggle_tracker_log'),
    path('list/<uuid:pk>/share-toggle/', views.ShareToggleView.as_view(), name='share_toggle'),
    path('settings/', views.ThemeSettingsView.as_view(), name='settings'),
    path('calendar/', views.CalendarView.as_view(), name='calendar'),
    path('calendar/feed/<uuid:token>/calendar.ics', api_views.PersonalICalFeedView.as_view(), name='list_ical_feed'),
    path('workout/log-session/', views.WorkoutLogSessionView.as_view(), name='workout_log_session'),
    path('workout/session/<int:session_id>/delete/', views.DeleteWorkoutSessionView.as_view(), name='workout_delete_session'),
]
