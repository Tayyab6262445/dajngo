from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from pymongo import MongoClient
from django.conf import settings
from bson.objectid import ObjectId

import certifi

# ✅ Get MongoDB URI from settings.py
MONGO_URI = getattr(settings, "MONGO_URI", "mongodb+srv://tayyab:angel123@cluster0.x7zaa.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

# ✅ Secure connection to MongoDB Atlas
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client["workshop"]  # Change this to your database name

# ✅ Collections
users_collection = db["users"]
tasks_collection = db["tasks"]
parts_collection = db["vehicle_parts"]
## add the parts
@csrf_exempt
def add_vehicle_part(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            # Extract required fields
            part_name = data.get("part_name")
            part_number = data.get("part_number")
            vehicle_model = data.get("vehicle_model")
            price = data.get("price")
            stock_quantity = data.get("stock_quantity")
            company_name = data.get("company_name")  # New field
            added_on = datetime.utcnow()  # Current date & time in UTC

            # ✅ Validate required fields
            required_fields = ["part_name", "part_number", "vehicle_model", "price", "stock_quantity", "company_name"]
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({"error": f"{field.replace('_', ' ').title()} is required"}, status=400)

            # ✅ Create part document
            part = {
                "part_name": part_name,
                "part_number": part_number,
                "vehicle_model": vehicle_model,
                "price": price,
                "stock_quantity": stock_quantity,
                "company_name": company_name,
                "added_on": added_on  # Store timestamp
            }

            # ✅ Insert into MongoDB
            result = parts_collection.insert_one(part)

            return JsonResponse({
                "message": "Vehicle part added successfully!",
                "part_id": str(result.inserted_id),
                "company_name": company_name,
                "added_on": added_on.strftime("%Y-%m-%d %H:%M:%S")  # Convert to string for response
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    return JsonResponse({"error": "Method not allowed"}, status=405)


## delete part
@csrf_exempt
def delete_vehicle_part(request, part_id):
    if request.method == "DELETE":
        try:
            # ✅ Check if part_id is a valid ObjectId
            if not ObjectId.is_valid(part_id):
                return JsonResponse({"error": "Invalid part ID format"}, status=400)

            # ✅ Find and delete the part from MongoDB
            result = parts_collection.delete_one({"_id": ObjectId(part_id)})

            if result.deleted_count == 0:
                return JsonResponse({"error": "Part not found"}, status=404)

            return JsonResponse({"message": "Vehicle part deleted successfully!"}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)




## fetch all the products
@csrf_exempt
def get_all_vehicle_parts(request):
    if request.method == "GET":
        try:
            # ✅ Retrieve all parts from MongoDB
            parts = list(parts_collection.find({}))

            if not parts:
                return JsonResponse({"message": "No vehicle parts found"}, status=404)

            # ✅ Convert ObjectId fields to string for JSON response
            for part in parts:
                part["_id"] = str(part["_id"])  # Convert ObjectId to string

            return JsonResponse(parts, safe=False, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)

## edit the part
@csrf_exempt
def update_vehicle_part(request, part_id):
    if request.method == "PUT":
        try:
            data = json.loads(request.body)

            # ✅ Validate part_id format
            if not ObjectId.is_valid(part_id):
                return JsonResponse({"error": "Invalid part ID format"}, status=400)

            # ✅ Check if the part exists
            part = parts_collection.find_one({"_id": ObjectId(part_id)})
            if not part:
                return JsonResponse({"error": "Part not found"}, status=404)

            # ✅ Fields that can be updated
            update_fields = {}
            allowed_fields = ["part_name", "part_number", "vehicle_model", "price", "stock_quantity", "company_name", "date_time"]

            for field in allowed_fields:
                if field in data:
                    update_fields[field] = data[field]

            if not update_fields:
                return JsonResponse({"error": "No valid fields provided for update"}, status=400)

            # ✅ Perform update
            parts_collection.update_one({"_id": ObjectId(part_id)}, {"$set": update_fields})

            return JsonResponse({
                "message": "Vehicle part updated successfully!",
                "updated_fields": update_fields
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)
