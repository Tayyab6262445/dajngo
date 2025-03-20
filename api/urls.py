from django.urls import path
from .views import signup, signin, get_user, update_user,get_all_users,create_task,get_tasks_by_user,get_task_by_id,delete_user,update_task,update_task_status,add_task_part,get_user_tasks_with_parts,get_pending_tasks_by_user,get_completed_tasks_by_user

urlpatterns = [
    path("signup/", signup, name="signup"),
    path("signin/", signin, name="signin"),
    path("user/<str:email>/", get_user, name="get_user"),
    path("user/<str:email>/update/", update_user, name="update_user"),
    path("users/", get_all_users, name="get_all_users"),
    path("tasks/create/", create_task, name="create_task"),
    path("tasks/user/<str:user_id>/", get_tasks_by_user, name="get_tasks_by_user"),
    path("tasks/<str:task_id>/", get_task_by_id, name="get_task_by_id"),
    path("user/<str:user_id>/delete/", delete_user, name="delete_user"),
    path("tasks/<str:task_id>/update/", update_task, name="update_task"),
    path("tasks/<str:task_id>/status/", update_task_status, name="update_task_status"),
    path("add-task-part/<str:task_id>/", add_task_part, name="add_task_part"),
    path("get-user-tasks/<str:user_id>/", get_user_tasks_with_parts, name="get_user_tasks_with_parts"),
    path('tasks/pending/<str:user_id>/', get_pending_tasks_by_user, name='get_pending_tasks_by_user'),
    path('tasks/completed/<str:user_id>/', get_completed_tasks_by_user, name='get_completed_tasks_by_user'),
    
   
     

]
  

