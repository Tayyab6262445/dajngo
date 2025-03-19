from django.urls import path
from .views import add_vehicle_part,delete_vehicle_part,get_all_vehicle_parts,update_vehicle_part

urlpatterns = [
    path("add-part/", add_vehicle_part, name="add_vehicle_part"),
     path("delete-part/<str:part_id>/", delete_vehicle_part, name="delete_vehicle_part"),
      path("get-all-parts/", get_all_vehicle_parts, name="get_all_vehicle_parts"),
       path("update-part/<str:part_id>/", update_vehicle_part, name="update_vehicle_part"),
]
