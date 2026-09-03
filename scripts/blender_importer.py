import bpy
import json
import os
import math

# Run this script inside Blender's scripting workspace.
# Ensure you have a sphere named "earth" and objects named "sat-0" through "sat-9".

JSON_PATH = os.path.join(bpy.path.abspath("//"), "data", "blender_export.json")
# If not saving the .blend file next to the repo, hardcode the absolute path:
# JSON_PATH = r"d:\coding\Hacathon Projects\SatQuery\data\blender_export.json"

def update_scene():
    if not os.path.exists(JSON_PATH):
        return 1.0 # Run again in 1s
        
    try:
        with open(JSON_PATH, 'r') as f:
            data = json.load(f)
            
        states = data.get("states", {})
        
        # Earth scaling factor to make it fit in blender grid nicely. 
        # Earth Radius = 6371km. Let's say 1 blender unit = 1000km.
        SCALE = 1000.0
        
        for sc_id, state in states.items():
            if sc_id in bpy.data.objects:
                obj = bpy.data.objects[sc_id]
                pos = state.get("position_km", [0, 0, 0])
                
                # Update location
                obj.location.x = pos[0] / SCALE
                obj.location.y = pos[1] / SCALE
                obj.location.z = pos[2] / SCALE
                
                # Add keyframe for animation if desired
                obj.keyframe_insert(data_path="location")
                
    except Exception as e:
        print(f"Error reading JSON: {e}")
        
    return 1.0 # Run every 1 second

# Register the timer
bpy.app.timers.register(update_scene)
print("SatQuery Blender Bridge Active. Polling blender_export.json...")
