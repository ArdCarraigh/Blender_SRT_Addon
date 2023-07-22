# -*- coding: utf-8 -*-
# tools/billboard_tools.py

import bpy
import os
import re
import numpy as np
from math import radians
from mathutils import Vector
from copy import deepcopy
from bpy_extras.object_utils import object_data_add
from io_mesh_srt.utils import GetCollection, JoinThem, selectOnly, ImportTemplates, GetLoopDataPerVertex

def generate_srt_billboards(context, number_billboards, bb_width, bb_bottom, bb_top, uvs = None):
    ImportTemplates()
    if number_billboards:
        horiz_coll = GetCollection("Horizontal Billboard")
        bb_coll = GetCollection("Vertical Billboards", True)
                
        # Get Horizontal Billboard Material if it exists           
        if horiz_coll:
            h_objects = horiz_coll.objects
            if h_objects:
                horiz_mat = h_objects[0].data.materials[0]

        bb_right = bb_width*0.5     
        bb_left = -bb_right
        angle_diff = 360/number_billboards
        
        # Material Creation
        if 'horiz_mat' not in locals():
            new_mat = bpy.data.materials["SRT_Material_Billboard_Template"].copy()
            new_mat.name = "SRT_Material_Billboard"
            
        # Geometry Nodes Creation
        node_group = bpy.data.node_groups["Billboard_Cutout_Template"].copy()
        node_group.name = "Billboard_Cutout"
        
        for i in range(number_billboards):
            verts = [[bb_left, 0, bb_bottom], [bb_right, 0, bb_bottom], [bb_right, 0, bb_top], [bb_left, 0, bb_top]]
            faces = [[0,1,2], [2,3,0]]
            # Add the mesh to the scene
            bb = bpy.data.meshes.new(name="Mesh_billboard"+str(i))
            bb.from_pydata(verts, [],faces)
            obj = object_data_add(context, bb)
            bb.shade_smooth()
            obj.rotation_euler[2] = radians(angle_diff * i)
            
            #SpeedTree Tag
            bb["SpeedTreeTag"] = 2
        
            # UV Map
            uv_map = bb.attributes.new("DiffuseUV", 'FLOAT2', 'CORNER')
            if uvs is not None:
                uv_map.data.foreach_set("vector", uvs[i])
                
            # Material Attribution
            if 'horiz_mat' in locals():
                bb.materials.append(horiz_mat)
            else:   
                bb.materials.append(new_mat)
            
            # Geometry Node Attribution
            geom_nodes = obj.modifiers.new(type='NODES', name = "Billboard_Cutout")
            geom_nodes.node_group = node_group
    
def generate_srt_horizontal_billboard(context, height = 0.5, size = 1, verts = None, uvs = None):
    ImportTemplates()
    vert_coll = horiz_coll = GetCollection("Vertical Billboards")
    bb_coll = GetCollection("Horizontal Billboard", True)
        
    # Get Vertical Billboard Material if it exists        
    if vert_coll:
        v_objects = vert_coll.objects
        if v_objects:
            vert_mat = v_objects[0].data.materials[0]
            
    # Material Creation
    if 'vert_mat' not in locals():
        new_mat = bpy.data.materials["SRT_Material_Billboard_Template"].copy()
        new_mat.name = "SRT_Material_Billboard"
        
    if not verts:
        right = size * 0.5
        left = -right
        verts = [[left, left, height], [right, left, height], [right, right, height], [left, right, height]]
    faces = [[0,1,2], [2,3,0]]
    # Add the mesh to the scene
    bb = bpy.data.meshes.new(name="Mesh_horizontal_billboard")
    bb.from_pydata(verts, [],faces)
    object_data_add(context, bb)
    bb.shade_smooth()
    
    #SpeedTree Tag
    bb["SpeedTreeTag"] = 2

    # UV Map
    uv_map = bb.attributes.new("DiffuseUV", 'FLOAT2', 'CORNER')
    if uvs is not None:
        uv_map.data.foreach_set("vector", uvs)
        
    # Material Attribution
    if 'vert_mat' in locals():   
        bb.materials.append(vert_mat) 
    else:
        bb.materials.append(new_mat)
        
def generate_srt_billboard_texture(context, resolution, margin, file_format = 'PNG', dds_dxgi = None, apply_texture = True, use_custom_path = False, custom_path = None):
    main_coll = GetCollection()
    if main_coll:
        bb_coll = None
        horiz_coll = None
        collision_coll = None
        lods_coll = []
        bb_objects = None
        horiz_objects = None
        objects = []
        for col in main_coll.children:
            col_name = col.name
            if re.search("Collision Objects", col_name):
                collision_coll = col
                collision_coll.hide_render = True
            if re.search("Vertical Billboards", col_name):
                bb_coll = col
                bb_coll.hide_render = True
            if re.search("Horizontal Billboard", col_name):
                horiz_coll = col
                horiz_coll.hide_render = True
            if re.search("LOD", col_name):
                lods_coll.append(col)
                if "LOD0" not in col_name:
                    col.hide_render = True
        
        # Make a UV Map and get billboards' proportions and uvs    
        if (bb_coll or horiz_coll) and lods_coll:
            if bb_coll and bb_coll.objects:
                bb_objects = re.findall(r"Mesh_billboard\d+\.?\d*", str([x.name for x in bb_coll.objects]))
            if horiz_coll:
                horiz_objects = horiz_coll.objects
                
            if bb_objects or horiz_objects:
                
                # Prepare LOD0 Collection
                lod0_coll = lods_coll[0]
                lod0_coll_name = lod0_coll.name
                lod0_coll_dot = lod0_coll_name.find(".")
                if lod0_coll_dot > -1:
                    lod0_coll_number = int(lod0_coll_name[lod0_coll_dot + 1:])
                else:
                    lod0_coll_number = 0
                JoinThem(lod0_coll.objects)
                lod0_mesh = lod0_coll.objects[0]
                lod0_modif = lod0_mesh.modifiers['Leaf_Card']
                
                # Import Normal MatCap
                ImportTemplates()
                
                # Get File Name and Directory
                if bb_objects:
                    billboard_mat_nodes = bb_coll.objects[bb_objects[0]].data.materials[0].node_tree.nodes
                elif horiz_objects:
                    billboard_mat_nodes = horiz_objects[0].data.materials[0].node_tree.nodes
                    
                # Get File Format
                is_dds = False
                if file_format == 'DDS':
                    from blender_dds_addon.directx.texconv import Texconv
                    texconv = Texconv()
                    is_dds = True
                    file_format = 'TARGA'
                path = os.path.dirname(billboard_mat_nodes["Diffuse Texture"].image.filepath)
                ext = ".png" if file_format == 'PNG' else ".tga"
                filename = "\\" + main_coll.name + "_Billboard" + ext
                filename_normal = "\\" + main_coll.name + "_Billboard_n" + ext
                
                # Prepare Compositing
                bpy.context.view_layer.use_pass_diffuse_color = True
                bpy.context.view_layer.use_pass_normal = True
                active_scene = bpy.context.scene
                active_scene.view_settings.view_transform = 'Standard'
                active_scene.render.film_transparent = True
                active_scene.render.engine = 'BLENDER_EEVEE'
                active_scene.use_nodes = True
                ntree = active_scene.node_tree
                nodes = ntree.nodes
                links = ntree.links
                composite = nodes["Composite"]
                composite.location.x = 5000
                mask = nodes.new('CompositorNodeMask')
                mask.size_source = 'FIXED'
                mask.size_x = resolution
                mask.size_y = resolution
                mask.location = (10, 650)
                key = nodes.new('CompositorNodeColorMatte')
                key.inputs['Key Color'].default_value = (0,0,0,0)
                key.location = (170, 650)
                viewer = nodes.new('CompositorNodeViewer')
                viewer.location = (5000, 200)
                file_output = nodes.new('CompositorNodeOutputFile')
                file_output.format.file_format = file_format
                file_output.file_slots.new('Image2')
                if use_custom_path and custom_path:
                    file_output.base_path = custom_path
                else:
                    file_output.base_path = path
                file_output.location = (5000, 0)
                links.new(mask.outputs['Mask'], key.inputs['Image'])
                
                # UV Unwrap
                if bb_objects:
                    objects.extend([bb_coll.objects[name] for name in bb_objects])
                if horiz_objects:
                    objects.append(horiz_objects[0])
                number_billboards = len(objects)
                bpy.context.view_layer.objects.active = None
                bpy.ops.object.select_all(action='DESELECT')
                for obj in objects:
                    bpy.context.view_layer.objects.active = obj
                    obj.select_set(state=True)
                bpy.ops.object.mode_set(mode='EDIT', toggle=False)
                bpy.ops.mesh.select_all(action="SELECT")
                bpy.ops.uv.unwrap(margin = margin / resolution)
                bpy.ops.mesh.select_all(action="DESELECT")
                bpy.ops.object.mode_set(mode='OBJECT')
                
                cameras = []
                scenes = []
                view_layers = []
                collections = []
                meshes = []
                geom_nodes = []
                for i, obj in enumerate(objects):
                    selectOnly(obj)
                    mesh = obj.data
                    verts = mesh.vertices
                    mesh.uv_layers[0].name = "DiffuseUV"
                    render_rotation = 0
                    
                    # Get UVs
                    uvs = np.array(GetLoopDataPerVertex(mesh, "UV", "DiffuseUV"))
                    uvs[:,1] = 1 - uvs[:,1]
                    uvs_x = uvs[:,0]
                    uvs_y = uvs[:,1]
                    uv_x_max = np.max(uvs_x)
                    uv_x_min = np.min(uvs_x)
                    uv_y_max = np.max(uvs_y)
                    uv_y_min = np.min(uvs_y)
                    uv_x_diff = uv_x_max - uv_x_min
                    uv_y_diff = uv_y_max - uv_y_min
                    
                    # Horizontal Billboard    
                    if i == number_billboards - 1 and horiz_objects:
                        loc = Vector((0,0,1))
                        billboard_dimensions = [verts[2].co[0] - verts[0].co[0], verts[2].co[1] - verts[0].co[1]]
                        origin_z = np.mean([verts[0].co[2], verts[2].co[2]])
                        active_scene.render.resolution_x = round(uv_x_diff * resolution)
                        active_scene.render.resolution_y = round(uv_y_diff * resolution)
                    
                    # Vertical Billboards
                    else:
                        rotation = deepcopy(obj.rotation_euler[2])
                        bpy.ops.object.transform_apply(rotation=True)
                        loc = deepcopy(verts[0].normal) #Get the normal without transforms
                        obj.rotation_euler[2] = -rotation
                        bpy.ops.object.transform_apply(rotation=True)
                        obj.rotation_euler[2] = rotation
                        bb_width = verts[2].co[0] - verts[0].co[0]
                        bb_top = verts[2].co[2]
                        bb_bottom = verts[0].co[2]
                        billboard_dimensions = [bb_width, bb_top - bb_bottom]
                        loc_z = (bb_top + bb_bottom)*0.5
                    
                        # Deal with UV Rotation and Resolution
                        if np.argmax([uv_x_diff, uv_y_diff]) != np.argmax(billboard_dimensions):
                            render_rotation = radians(90)
                            uvs[0] = [uv_x_max, uv_y_max]
                            uvs[1] = [uv_x_max, uv_y_min]
                            uvs[2] = [uv_x_min, uv_y_min]
                            uvs[3] = [uv_x_min, uv_y_max]
                            uv_array = uvs[[0,1,2,2,3,0]].flatten()
                            mesh.attributes["DiffuseUV"].data.foreach_set("vector", uv_array)
                            active_scene.render.resolution_x = round(uv_y_diff * resolution)
                            active_scene.render.resolution_y = round(uv_x_diff * resolution)
                        else:
                            uvs[0] = [uv_x_min, uv_y_min]
                            uvs[1] = [uv_x_max, uv_y_min]
                            uvs[2] = [uv_x_max, uv_y_max]
                            uvs[3] = [uv_x_min, uv_y_max]
                            uv_array = uvs[[0,1,2,2,3,0]].flatten()
                            mesh.attributes["DiffuseUV"].data.foreach_set("vector", uv_array)
                            active_scene.render.resolution_x = round(uv_x_diff * resolution)
                            active_scene.render.resolution_y = round(uv_y_diff * resolution)
                            
                    # Make a New Scene and View Layer for Each Billboard
                    scene = active_scene.copy()
                    scenes.append(scene)
                    bpy.context.window.scene = scene
                    view_layer = bpy.context.view_layer
                    view_layer.name = "ViewLayer" + str(i+1)
                    view_layers.append(view_layer)
                        
                    # Camera Distance
                    dist = np.max(billboard_dimensions)
                    #distance = dist * 0.5 / 0.36
                    distance = dist * 1.25
                    
                    # Place Cameras
                    if i == number_billboards - 1 and horiz_objects:
                        distance += origin_z
                        loc.length = distance
                        bpy.ops.object.camera_add(location = loc, rotation = [0, 0, 0])
                    else:
                        loc.length = distance
                        loc[2] = loc_z
                        bpy.ops.object.camera_add(location = loc, rotation = [np.pi*0.5, 0, rotation])
                    cam = bpy.context.active_object
                    cameras.append(cam)
                    cam.data.type = 'ORTHO'
                    cam.data.ortho_scale = dist
                    scene.camera = cam
                    
                    # Make a New Collection for Each Billboard (Necessary for Facing Leaves...)
                    lod0_coll_number += 1
                    new_coll = GetCollection("LOD" + str(lod0_coll_number * 0.001), True, False)
                    collections.append(new_coll)
                    selectOnly(lod0_mesh)
                    bpy.ops.object.duplicate(linked=False, mode='TRANSLATION')
                    new_mesh = bpy.context.active_object
                    meshes.append(new_mesh)
                    new_coll.objects.link(new_mesh)
                    lod0_coll.objects.unlink(new_mesh)
                    new_geom_nodes = lod0_modif.node_group.copy()
                    geom_nodes.append(new_geom_nodes)
                    new_mesh.modifiers['Leaf_Card'].node_group = new_geom_nodes
                    new_mesh.modifiers['Leaf_Card'].node_group.nodes['Camera'].inputs['Object'].default_value = cam
                    
                    # Make the compositing
                    y_coord = 400 - 400 * i
                    color_ramp = nodes.new('CompositorNodeValToRGB')
                    #color_ramp.color_ramp.elements[0].position = 0.495
                    #color_ramp.color_ramp.elements[1].position = 0.505
                    color_ramp.location = (500, y_coord)
                    set_alpha = nodes.new('CompositorNodeSetAlpha')
                    set_alpha.location = (800, y_coord)
                    transform = nodes.new('CompositorNodeTransform')
                    transform.inputs['X'].default_value = (((uv_x_max + uv_x_min) * 0.5) - 0.5) * resolution
                    transform.inputs['Y'].default_value = (((uv_y_max + uv_y_min) * 0.5) - 0.5) * resolution
                    transform.inputs['Angle'].default_value = render_rotation
                    transform.location = (1200, y_coord)
                    alpha_over = nodes.new('CompositorNodeAlphaOver')
                    alpha_over.location = (1500 + 200 * i, y_coord)
                    links.new(color_ramp.outputs['Image'], set_alpha.inputs['Alpha'])
                    links.new(set_alpha.outputs['Image'], transform.inputs['Image'])
                    links.new(transform.outputs['Image'], alpha_over.inputs[2])
                    #If Rotated
                    if render_rotation:
                        flip = nodes.new('CompositorNodeFlip')
                        flip.location = (1000, y_coord)
                        
                    # Render nodes
                    if not i:
                        nodes['Render Layers'].scene = scene
                        nodes['Render Layers'].layer = view_layer.name
                        links.new(key.outputs['Image'], alpha_over.inputs[1])
                        links.new(nodes['Render Layers'].outputs['DiffCol'], set_alpha.inputs['Image'])
                        links.new(nodes['Render Layers'].outputs['Alpha'], color_ramp.inputs['Fac'])
                    else:
                        render_node = nodes.new('CompositorNodeRLayers')
                        render_node.location = (10, y_coord)
                        render_node.scene = scene
                        render_node.layer = view_layer.name
                        links.new(alpha_over_previous.outputs['Image'], alpha_over.inputs[1])
                        links.new(render_node.outputs['DiffCol'], set_alpha.inputs['Image'])
                        links.new(render_node.outputs['Alpha'], color_ramp.inputs['Fac'])
                    # Rotation
                    if render_rotation:
                        links.new(set_alpha.outputs['Image'], flip.inputs['Image'])
                        links.new(flip.outputs['Image'], transform.inputs['Image'])
                    # File Output
                    if i == number_billboards - 1:
                        links.new(alpha_over.outputs['Image'], composite.inputs['Image'])
                        links.new(alpha_over.outputs['Image'], viewer.inputs['Image'])
                        links.new(alpha_over.outputs['Image'], file_output.inputs[0])
                        alpha_over_normal = nodes.new('CompositorNodeAlphaOver')
                        alpha_over_normal.inputs[1].default_value = (0.219525, 0.21586, 1, 1)
                        alpha_over_normal.location = (4000, y_coord)
                        links.new(alpha_over.outputs['Image'], alpha_over_normal.inputs[2])
                        links.new(alpha_over_normal.outputs['Image'], file_output.inputs[1])
                        # Make a last unused camera and render otherwise the last render doesn't show up for some reason
                        scene = active_scene.copy()
                        scenes.append(scene)
                        bpy.ops.object.camera_add(location = (0,0,0), rotation = (0,0,0))
                        cam = bpy.context.active_object
                        cameras.append(cam)
                        scene.camera = cam
                        render_node = nodes.new('CompositorNodeRLayers')
                        render_node.location = (10, y_coord - 370)
                        render_node.scene = scene
                            
                    alpha_over_previous = alpha_over
                
                # Make a Diffuse Color Render for Each Billboard    
                for i,_ in enumerate(objects):
                    bpy.context.window.scene = scenes[i]
                    GetCollection(lod0_coll_name, make_active = True)
                    bpy.context.scene.view_layers[view_layers[i].name].active_layer_collection.exclude = True
                    for j,_ in enumerate(collections):
                        if collections[i] != collections[j]:
                            GetCollection(collections[j].name, make_active = True)
                            bpy.context.view_layer.active_layer_collection.exclude = True
                    bpy.ops.render.render(scene = scenes[i].name)
                    # Render last unused scene
                    if i == number_billboards - 1:
                        bpy.ops.render.render(scene = scenes[-1].name)
                        
                # Rename the Diffuse file        
                old_name = "\\Image0001" + ext
                placeholder_name = "\\Image20001" + ext
                old_path = custom_path + old_name if use_custom_path and custom_path else path + old_name
                new_path = custom_path + filename if use_custom_path and custom_path else path + filename
                placeholder_path = custom_path + placeholder_name if use_custom_path and custom_path else path + placeholder_name
                os.remove(placeholder_path)
                try:
                    os.rename(old_path, new_path)
                except FileExistsError:
                    os.remove(new_path)
                    os.rename(old_path, new_path)
                        
                # Make a Normal Render for Each Billboard
                for i,_ in enumerate(objects):
                    old_mats = meshes[i].data.materials
                    for j, mat in enumerate(old_mats):
                        
                        # Deal with Matcap Material
                        matcap = bpy.data.materials["NORMAL_MATCAP_DIRECT_X_TEMPLATE"].copy()
                        matcap.name = "NORMAL_MATCAP_DIRECT_X"
                        matcap_ntree = matcap.node_tree
                        matcap_links = matcap_ntree.links
                        matcap_nodes = matcap_ntree.nodes
                        if mat["EBranchSeamSmoothing"] == 'EFFECT_OFF':
                            for link in matcap_nodes["Branch Seam Weight Mult"].outputs['Value'].links:
                                matcap_links.remove(link)      
                        diffuse_texture = mat.node_tree.nodes["Diffuse Texture"].image
                        matcap_nodes["Branch Seam Diffuse Texture"].image = diffuse_texture
                        matcap_nodes["Diffuse Texture"].image = diffuse_texture
                        matcap_nodes["Alpha Scalar"].outputs["Value"].default_value = mat.node_tree.nodes["Alpha Scalar"].outputs["Value"].default_value
                        normal_texture = mat.node_tree.nodes["Normal Texture"].image
                        detail_normal_texture = mat.node_tree.nodes["Detail Normal Texture"].image
                        if not normal_texture:
                            matcap_links.remove(matcap_nodes["Bump"].inputs['Height'].links[0])
                            matcap_links.remove(matcap_nodes["Bump"].inputs['Normal'].links[0])
                        else:
                            matcap_nodes["Normal Texture"].image = normal_texture
                            matcap_nodes["Branch Seam Normal Texture"].image = normal_texture
                            matcap_nodes["Detail Normal Texture"].image = detail_normal_texture
                            matcap_nodes["Branch Seam Detail Normal Texture"].image = detail_normal_texture
                            if mat["EDetailLayer"] == 'EFFECT_OFF':
                                matcap_links.remove(matcap_nodes["Mix Detail Normal"].inputs['Fac'].links[0])
                        old_mats[j] = matcap
                    
                    bpy.ops.render.render(scene = scenes[i].name)
                    # Render last unused scene
                    if i == number_billboards - 1:
                        bpy.ops.render.render(scene = scenes[-1].name)

                # Rename the Normal file
                old_name = "\\Image20001" + ext
                placeholder_name = "\\Image0001" + ext
                old_path = custom_path + old_name if use_custom_path and custom_path else path + old_name
                new_path_normal = custom_path + filename_normal if use_custom_path and custom_path else path + filename_normal
                placeholder_path = custom_path + placeholder_name if use_custom_path and custom_path else path + placeholder_name
                os.remove(placeholder_path)
                try:
                    os.rename(old_path, new_path_normal)
                except FileExistsError:
                    os.remove(new_path_normal)
                    os.rename(old_path, new_path_normal)
                    
                # Convert to DDS if requested
                if is_dds:
                    texconv.convert_to_dds(file = new_path, dds_fmt = dds_dxgi, out = path)
                    texconv.convert_to_dds(file = new_path_normal, dds_fmt = dds_dxgi, out = path)
                    texconv.unload_dll()
                    os.remove(new_path)
                    os.remove(new_path_normal)
                    new_path = new_path[:-3] + "dds"
                    new_path_normal = new_path_normal[:-3] + "dds"
                    filename = filename[:-3] + "dds"
                    filename_normal = filename_normal[:-3] + "dds"
                
                # Apply new textures if requested
                if apply_texture:
                    image_to_remove = bpy.data.images.get(filename[1:])
                    if image_to_remove:
                        bpy.data.images.remove(image_to_remove)
                    image_to_remove = bpy.data.images.get(filename_normal[1:])
                    if image_to_remove:
                        bpy.data.images.remove(image_to_remove)
                    if is_dds:
                        from blender_dds_addon.ui.import_dds import load_dds
                        image = load_dds(new_path)
                        image.name += ".dds"
                        image.filepath = new_path
                        image.colorspace_settings.name = 'sRGB'
                        billboard_mat_nodes["Diffuse Texture"].image = image
                        billboard_mat_nodes["Branch Seam Diffuse Texture"].image = image
                        image_normal = load_dds(new_path_normal)
                        image_normal.name += ".dds"
                        image_normal.filepath = new_path_normal
                        image_normal.colorspace_settings.name = 'Non-Color'
                        billboard_mat_nodes["Normal Texture"].image = image_normal
                        billboard_mat_nodes["Branch Seam Normal Texture"].image = image_normal
                    else:
                        billboard_mat_nodes["Diffuse Texture"].image = bpy.data.images.load(new_path)
                        billboard_mat_nodes["Diffuse Texture"].image.colorspace_settings.name = 'sRGB'
                        billboard_mat_nodes["Branch Seam Diffuse Texture"].image = bpy.data.images.load(new_path, check_existing = True)
                        billboard_mat_nodes["Normal Texture"].image = bpy.data.images.load(new_path_normal)
                        billboard_mat_nodes["Normal Texture"].image.colorspace_settings.name = 'Non-Color'
                        billboard_mat_nodes["Branch Seam Normal Texture"].image = bpy.data.images.load(new_path_normal, check_existing = True)
                
                # Clean up
                for node in nodes:
                    if node != nodes["Composite"] and node != nodes['Render Layers']:
                        nodes.remove(node)
                for i,_ in enumerate(objects):
                    bpy.data.collections.remove(collections[i])
                for i in reversed(range(len(scenes))):
                    bpy.data.scenes.remove(scenes[i])
                    bpy.data.objects.remove(cameras[i])
                        
                # Purge orphan data left unused
                override = bpy.context.copy()
                override["area.type"] = ['OUTLINER']
                override["display_mode"] = ['ORPHAN_DATA']
                bpy.ops.outliner.orphans_purge(override)
                        
                GetCollection()
                                  
    return   