# -*- coding: utf-8 -*-
# tools/billboard_tools.py

import bpy
import os
import re
import numpy as np
from math import radians
from mathutils import Vector
from copy import deepcopy
from shutil import rmtree
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
        angle_diff = 360 / number_billboards
        
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
            
            # Rotation
            obj.rotation_euler[2] = radians(90 + angle_diff * i)
            
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
        
def generate_srt_billboard_texture(context, resolution, margin, dilation, file_format = 'PNG', dds_dxgi = None, apply_texture = True, use_custom_path = False, custom_path = None):
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
                col.hide_render = True
        
        # Make a UV Map and get billboards' proportions and uvs    
        if (bb_coll or horiz_coll) and lods_coll:
            if bb_coll and bb_coll.objects:
                bb_objects = re.findall(r"Mesh_billboard\d+\.?\d*", str([x.name for x in bb_coll.objects]))
            if horiz_coll:
                horiz_objects = horiz_coll.objects
                
            if bb_objects or horiz_objects:
                
                # Make a Temporary Collection
                last_lod_col = lods_coll[-1]
                JoinThem(last_lod_col.objects)
                temp_coll = GetCollection("LOD100", True, False)
                selectOnly(last_lod_col.objects[0])
                bpy.ops.object.duplicate(linked=False, mode='TRANSLATION')
                temp_mesh = bpy.context.active_object
                old_mats = temp_mesh.data.materials
                temp_coll.objects.link(temp_mesh)
                last_lod_col.objects.unlink(temp_mesh)
                
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
                    is_dds = True
                    file_format = 'TARGA'
                path = os.path.dirname(billboard_mat_nodes["Diffuse Texture"].image.filepath)
                ext = ".png" if file_format == 'PNG' else ".tga"
                filename = "\\" + main_coll.name + "_Billboard" + ext
                filename_normal = "\\" + main_coll.name + "_Billboard_n" + ext
                
                # Prepare Scene and View Layer
                temp_scene = bpy.context.scene.copy()
                bpy.context.window.scene = temp_scene
                view_layer = bpy.context.view_layer
                view_layer.use_pass_diffuse_color = True
                view_layer.use_pass_shadow = True
                view_layer.use_pass_mist = True
                temp_scene.view_settings.view_transform = 'Standard'
                temp_scene.render.film_transparent = True
                temp_scene.render.engine = 'BLENDER_EEVEE'
                temp_scene.use_nodes = True
                ntree = temp_scene.node_tree
                nodes = ntree.nodes
                links = ntree.links
                
                #Compositing
                render_node = nodes['Render Layers']
                render_node.scene = temp_scene
                render_node.layer = view_layer.name
                set_alpha = nodes.new('CompositorNodeSetAlpha')
                set_alpha.mode = 'REPLACE_ALPHA'
                mix = nodes.new('CompositorNodeMixRGB')
                mix.blend_type = 'MULTIPLY'
                mix.inputs['Fac'].default_value = 0.65
                separate_color = nodes.new('CompositorNodeSeparateColor')
                dilate_red = nodes.new('CompositorNodeDilateErode')
                dilate_red.mode = 'DISTANCE'
                dilate_red.distance = dilation
                dilate_green = nodes.new('CompositorNodeDilateErode')
                dilate_green.mode = 'DISTANCE'
                dilate_green.distance = dilation
                dilate_blue = nodes.new('CompositorNodeDilateErode')
                dilate_blue.mode = 'DISTANCE'
                dilate_blue.distance = dilation
                combine_color = nodes.new('CompositorNodeCombineColor')
                alpha_over = nodes.new('CompositorNodeAlphaOver')
                file_output = nodes.new('CompositorNodeOutputFile')
                file_output.file_slots.new('Image2')
                if use_custom_path and custom_path:
                    temp_path = os.path.join(custom_path, "speedtree_temp")
                    os.makedirs(temp_path)
                    file_output.base_path = temp_path
                else:
                    temp_path = os.path.join(path, "speedtree_temp")
                    os.makedirs(temp_path)
                    file_output.base_path = temp_path
                    
                links.new(render_node.outputs['DiffCol'], mix.inputs[1])
                links.new(render_node.outputs['Shadow'], mix.inputs[2])
                links.new(mix.outputs['Image'], set_alpha.inputs['Image'])
                links.new(render_node.outputs['Alpha'], set_alpha.inputs['Alpha'])
                links.new(mix.outputs['Image'], separate_color.inputs['Image'])
                links.new(separate_color.outputs['Red'], dilate_red.inputs['Mask'])
                links.new(separate_color.outputs['Green'], dilate_green.inputs['Mask'])
                links.new(separate_color.outputs['Blue'], dilate_blue.inputs['Mask'])
                links.new(dilate_red.outputs['Mask'], combine_color.inputs['Red'])
                links.new(dilate_green.outputs['Mask'], combine_color.inputs['Green'])
                links.new(dilate_blue.outputs['Mask'], combine_color.inputs['Blue'])
                links.new(combine_color.outputs['Image'], alpha_over.inputs[1])
                links.new(set_alpha.outputs['Image'], alpha_over.inputs[2])
                links.new(alpha_over.outputs['Image'], file_output.inputs[0])
                links.new(render_node.outputs['Alpha'], file_output.inputs[1])
                
                # Add Sun
                bpy.ops.object.light_add(type='SUN')
                sun = bpy.context.active_object
                
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
                
                # First Renders - Diffuse + Alpha
                cameras = []
                stored_uvs = []
                rotations = []
                for i,_ in enumerate(old_mats):
                    old_mats[i] = old_mats[i].copy()
                    old_mats[i].shadow_method = 'OPAQUE'
                for i, obj in enumerate(objects):
                    selectOnly(obj)
                    mesh = obj.data
                    verts = mesh.vertices
                    mesh.uv_layers[0].name = "DiffuseUV"
                    rotations.append(0)
                    
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
                    stored_uvs.append([uv_x_max, uv_x_min, uv_y_max, uv_y_min])
                    
                    # Horizontal Billboard    
                    if i == number_billboards - 1 and horiz_objects:
                        loc = Vector((0,0,1))
                        billboard_dimensions = [verts[2].co[0] - verts[0].co[0], verts[2].co[1] - verts[0].co[1]]
                        origin_z = np.mean([verts[0].co[2], verts[2].co[2]])
                        temp_scene.render.resolution_x = round(uv_x_diff * resolution)
                        temp_scene.render.resolution_y = round(uv_y_diff * resolution)
                    
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
                            rotations[-1] = radians(90)
                            uvs[0] = [uv_x_max, uv_y_max]
                            uvs[1] = [uv_x_max, uv_y_min]
                            uvs[2] = [uv_x_min, uv_y_min]
                            uvs[3] = [uv_x_min, uv_y_max]
                            uv_array = uvs[[1,0,3,3,2,1]].flatten()
                            mesh.attributes["DiffuseUV"].data.foreach_set("vector", uv_array)
                            temp_scene.render.resolution_x = round(uv_y_diff * resolution)
                            temp_scene.render.resolution_y = round(uv_x_diff * resolution)
                        else:
                            uvs[0] = [uv_x_min, uv_y_min]
                            uvs[1] = [uv_x_max, uv_y_min]
                            uvs[2] = [uv_x_max, uv_y_max]
                            uvs[3] = [uv_x_min, uv_y_max]
                            uv_array = uvs[[0,1,2,2,3,0]].flatten()
                            mesh.attributes["DiffuseUV"].data.foreach_set("vector", uv_array)
                            temp_scene.render.resolution_x = round(uv_x_diff * resolution)
                            temp_scene.render.resolution_y = round(uv_y_diff * resolution)
                    
                    # Place Cameras
                    if i == number_billboards - 1 and horiz_objects:
                        loc.length = billboard_dimensions[0] * 2 + origin_z
                        bpy.ops.object.camera_add(location = loc, rotation = [0, 0, 0])
                    else:
                        loc.length = billboard_dimensions[0] * 2
                        loc[2] = loc_z
                        bpy.ops.object.camera_add(location = loc, rotation = [np.pi*0.5, 0, rotation])
                    cam = bpy.context.active_object
                    cameras.append(cam)
                    cam.data.type = 'ORTHO'
                    cam.data.ortho_scale = np.max(billboard_dimensions)
                    temp_scene.camera = cam
                    
                    # Render
                    file_output.file_slots[0].path = "temp_diffuse_" + str(i)
                    file_output.file_slots[1].path = "temp_alpha_" + str(i)
                    bpy.ops.render.render(scene = temp_scene.name)
                    
                # Second Renders - Ambient
                links.new(render_node.outputs['DiffCol'], set_alpha.inputs['Image'])
                links.new(render_node.outputs['DiffCol'], separate_color.inputs['Image'])
                file_output.file_slots.remove(file_output.inputs[1])
                for mat in old_mats:
                    mat_tree = mat.node_tree
                    mat_nodes = mat_tree.nodes
                    mat_tree.links.new(mat_nodes['Ambient Color'].outputs['Color'], mat_nodes['Specular BSDF'].inputs['Base Color'])
                
                #Render
                for i, cam in enumerate(cameras):
                    temp_scene.camera = cam
                    file_output.file_slots[0].path = "temp_ambient_" + str(i)
                    bpy.ops.render.render(scene = temp_scene.name)
                    
                # Third Renders - Normals
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
                
                #Render
                for i, cam in enumerate(cameras):
                    temp_scene.camera = cam
                    file_output.file_slots[0].path = "temp_normal_" + str(i)
                    bpy.ops.render.render(scene = temp_scene.name)
                    
                # Assemble the Textures
                temp_bg = bpy.data.images.new("Untitled", resolution, resolution)
                bg = nodes.new('CompositorNodeImage')
                bg.image = temp_bg
                for i in range(len(cameras)):
                    rgb = nodes.new('CompositorNodeImage')
                    rgb.image = bpy.data.images.load(temp_path + "\\temp_diffuse_" + str(i) + "0001.png", check_existing = True)
                    transform_rgb = nodes.new('CompositorNodeTransform')
                    transform_rgb.inputs['X'].default_value = (((stored_uvs[i][0] + stored_uvs[i][1]) * 0.5) - 0.5) * resolution
                    transform_rgb.inputs['Y'].default_value = (((stored_uvs[i][2] + stored_uvs[i][3]) * 0.5) - 0.5) * resolution
                    transform_rgb.inputs['Angle'].default_value = rotations[i]
                    alpha_over_rgb = nodes.new('CompositorNodeAlphaOver')
                    alpha = nodes.new('CompositorNodeImage')
                    alpha.image = bpy.data.images.load(temp_path + "\\temp_alpha_" + str(i) + "0001.png", check_existing = True)
                    transform_alpha = nodes.new('CompositorNodeTransform')
                    transform_alpha.inputs['X'].default_value = (((stored_uvs[i][0] + stored_uvs[i][1]) * 0.5) - 0.5) * resolution
                    transform_alpha.inputs['Y'].default_value = (((stored_uvs[i][2] + stored_uvs[i][3]) * 0.5) - 0.5) * resolution
                    transform_alpha.inputs['Angle'].default_value = rotations[i]
                    alpha_over_alpha = nodes.new('CompositorNodeAlphaOver')
                    normal = nodes.new('CompositorNodeImage')
                    normal.image = bpy.data.images.load(temp_path + "\\temp_normal_" + str(i) + "0001.png", check_existing = True)
                    transform_normal = nodes.new('CompositorNodeTransform')
                    transform_normal.inputs['X'].default_value = (((stored_uvs[i][0] + stored_uvs[i][1]) * 0.5) - 0.5) * resolution
                    transform_normal.inputs['Y'].default_value = (((stored_uvs[i][2] + stored_uvs[i][3]) * 0.5) - 0.5) * resolution
                    transform_normal.inputs['Angle'].default_value = rotations[i]
                    alpha_over_normal = nodes.new('CompositorNodeAlphaOver')
                    ambient = nodes.new('CompositorNodeImage')
                    ambient.image = bpy.data.images.load(temp_path + "\\temp_ambient_" + str(i) + "0001.png", check_existing = True)
                    transform_ambient = nodes.new('CompositorNodeTransform')
                    transform_ambient.inputs['X'].default_value = (((stored_uvs[i][0] + stored_uvs[i][1]) * 0.5) - 0.5) * resolution
                    transform_ambient.inputs['Y'].default_value = (((stored_uvs[i][2] + stored_uvs[i][3]) * 0.5) - 0.5) * resolution
                    transform_ambient.inputs['Angle'].default_value = rotations[i]
                    alpha_over_ambient = nodes.new('CompositorNodeAlphaOver')
                    
                    links.new(rgb.outputs['Image'], transform_rgb.inputs['Image'])
                    links.new(alpha.outputs['Image'], transform_alpha.inputs['Image'])
                    links.new(normal.outputs['Image'], transform_normal.inputs['Image'])
                    links.new(ambient.outputs['Image'], transform_ambient.inputs['Image'])
                    links.new(transform_rgb.outputs['Image'], alpha_over_rgb.inputs[2])
                    links.new(transform_alpha.outputs['Image'], alpha_over_alpha.inputs[2])
                    links.new(transform_normal.outputs['Image'], alpha_over_normal.inputs[2])
                    links.new(transform_ambient.outputs['Image'], alpha_over_ambient.inputs[2])
                    if not i:
                        links.new(bg.outputs['Image'], alpha_over_rgb.inputs[1])
                        links.new(bg.outputs['Image'], alpha_over_alpha.inputs[1])
                        links.new(bg.outputs['Image'], alpha_over_normal.inputs[1])
                        links.new(bg.outputs['Image'], alpha_over_ambient.inputs[1])
                    else:
                        links.new(alpha_over_previous_rgb.outputs['Image'], alpha_over_rgb.inputs[1])
                        links.new(alpha_over_previous_alpha.outputs['Image'], alpha_over_alpha.inputs[1])
                        links.new(alpha_over_previous_normal.outputs['Image'], alpha_over_normal.inputs[1])
                        links.new(alpha_over_previous_ambient.outputs['Image'], alpha_over_ambient.inputs[1])
                    alpha_over_previous_rgb = alpha_over_rgb
                    alpha_over_previous_alpha = alpha_over_alpha
                    alpha_over_previous_normal = alpha_over_normal
                    alpha_over_previous_ambient = alpha_over_ambient
                
                set_alpha_diffuse = nodes.new('CompositorNodeSetAlpha')
                #set_alpha_diffuse.mode = 'REPLACE_ALPHA'
                set_alpha_normal = nodes.new('CompositorNodeSetAlpha')
                #set_alpha_normal.mode = 'REPLACE_ALPHA'
                file_output.base_path = custom_path if use_custom_path and custom_path else path
                file_output.format.file_format = file_format
                file_output.file_slots[0].path = "temp_billboard"
                file_output.file_slots.new('temp_billboard_n')
                
                links.new(alpha_over_rgb.outputs['Image'], set_alpha_diffuse.inputs[0])
                links.new(alpha_over_alpha.outputs['Image'], set_alpha_diffuse.inputs[1])
                links.new(alpha_over_normal.outputs['Image'], set_alpha_normal.inputs[0])
                links.new(alpha_over_ambient.outputs['Image'], set_alpha_normal.inputs[1])
                links.new(set_alpha_diffuse.outputs['Image'], file_output.inputs[0])
                links.new(set_alpha_normal.outputs['Image'], file_output.inputs[1])
                
                # Render
                bpy.ops.render.render(scene = temp_scene.name)
                
                # Rename the files
                old_name_diff = "\\temp_billboard0001" + ext
                old_name_normal = "\\temp_billboard_n0001" + ext
                old_path_diff = custom_path + old_name_diff if use_custom_path and custom_path else path + old_name_diff
                old_path_normal = custom_path + old_name_normal if use_custom_path and custom_path else path + old_name_normal
                new_path_diff = custom_path + filename if use_custom_path and custom_path else path + filename
                new_path_normal = custom_path + filename_normal if use_custom_path and custom_path else path + filename_normal
                try:
                    os.rename(old_path_diff, new_path_diff)
                except FileExistsError:
                    os.remove(new_path_diff)
                    os.rename(old_path_diff, new_path_diff)
                try:
                    os.rename(old_path_normal, new_path_normal)
                except FileExistsError:
                    os.remove(new_path_normal)
                    os.rename(old_path_normal, new_path_normal)
                    
                # Convert to DDS if requested
                if is_dds:
                    texconv = Texconv()
                    texconv.convert_to_dds(file = new_path_diff, dds_fmt = dds_dxgi, out = path)
                    texconv.unload_dll()
                    texconv = Texconv()
                    texconv.convert_to_dds(file = new_path_normal, dds_fmt = dds_dxgi, out = path)
                    texconv.unload_dll()
                    os.remove(new_path_diff)
                    os.remove(new_path_normal)
                    new_path_diff = new_path_diff[:-3] + "dds"
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
                        image = load_dds(new_path_diff)
                        image.name += ".dds"
                        image.filepath = new_path_diff
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
                        image = bpy.data.images.load(new_path_diff)
                        image.colorspace_settings.name = 'sRGB'
                        billboard_mat_nodes["Diffuse Texture"].image = image
                        billboard_mat_nodes["Branch Seam Diffuse Texture"].image = image
                        image_normal = bpy.data.images.load(new_path_normal)
                        image_normal.colorspace_settings.name = 'Non-Color'
                        billboard_mat_nodes["Normal Texture"].image = image_normal
                        billboard_mat_nodes["Branch Seam Normal Texture"].image = image_normal
                
                # Clean up
                rmtree(temp_path)
                bpy.data.objects.remove(sun)
                bpy.data.scenes.remove(temp_scene)
                bpy.data.collections.remove(temp_coll)
                bpy.data.images.remove(temp_bg)
                for cam in cameras:
                    bpy.data.objects.remove(cam)
      
                # Purge orphan data left unused
                override = bpy.context.copy()
                override["area.type"] = ['OUTLINER']
                override["display_mode"] = ['ORPHAN_DATA']
                with bpy.context.temp_override(**override):
                    bpy.ops.outliner.orphans_purge()
                        
                GetCollection()
                                  
    return   