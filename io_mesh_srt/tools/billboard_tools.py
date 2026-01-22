# -*- coding: utf-8 -*-
# tools/billboard_tools.py

import bpy
import os
import re
import numpy as np
from glob import glob
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
            obj["SpeedTreeTag"] = 2
        
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
    obj = object_data_add(context, bb)
    bb.shade_smooth()
    
    #SpeedTree Tag
    obj["SpeedTreeTag"] = 2

    # UV Map
    uv_map = bb.attributes.new("DiffuseUV", 'FLOAT2', 'CORNER')
    if uvs is not None:
        uv_map.data.foreach_set("vector", uvs)
        
    # Material Attribution
    if 'vert_mat' in locals():   
        bb.materials.append(vert_mat) 
    else:
        bb.materials.append(new_mat)
        
def generate_srt_billboard_texture(context, resolution, margin, dilation, shadows_method = '0', file_format = 'PNG', dds_dxgi = None, apply_texture = True, use_custom_path = False, custom_path = None):
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
                old_mats_backup = list(old_mats)
                temp_coll.objects.link(temp_mesh)
                last_lod_col.objects.unlink(temp_mesh)
                
                # Import Normal MatCap
                ImportTemplates()
                
                # Get File Name and Directory
                if bb_objects:
                    billboard_mat = bb_coll.objects[bb_objects[0]].data.materials[0]
                    billboard_mat_nodes = billboard_mat.node_tree.nodes
                elif horiz_objects:
                    billboard_mat = horiz_objects[0].data.materials[0]
                    billboard_mat_nodes = billboard_mat.node_tree.nodes
                    
                # Get File Format
                is_dds = False
                if file_format == 'DDS':
                    from blender_dds_addon.directx.texconv import Texconv
                    is_dds = True
                    file_format = 'TARGA'
                diff_tex = billboard_mat_nodes["Diffuse Texture"].image
                if use_custom_path and custom_path:
                    path = custom_path
                else:
                    path = os.path.dirname(diff_tex.filepath) if diff_tex else "/tmp/"
                ext = ".png" if file_format == 'PNG' else ".tga"
                filename = "\\" + main_coll.name + "_Billboard" + ext
                filename_normal = "\\" + main_coll.name + "_Billboard_n" + ext
                
                # Prepare Scene and View Layer
                temp_scene = bpy.context.scene.copy()
                bpy.context.window.scene = temp_scene
                view_layer = bpy.context.view_layer
                view_layer.use_pass_diffuse_color = True
                view_layer.use_pass_shadow = True
                temp_scene.render.engine = 'BLENDER_EEVEE'
                temp_scene.display_settings.display_device = 'sRGB'
                temp_scene.view_settings.view_transform = 'Standard'
                temp_scene.render.film_transparent = True
                ntree = bpy.data.node_groups.new("SRT Billboard Comp", "CompositorNodeTree")
                temp_scene.compositing_node_group = ntree
                nodes = ntree.nodes
                links = ntree.links
                
                #Compositing
                render_node = nodes.new('CompositorNodeRLayers')
                render_node.scene = temp_scene
                render_node.layer = view_layer.name
                diff_adjust = nodes.new('CompositorNodeHueSat')
                diff_adjust.inputs["Value"].default_value = 1.1 # Adjust Here
                set_alpha = nodes.new('CompositorNodeSetAlpha')
                set_alpha.inputs["Type"].default_value = 'Replace Alpha'
                separate_color = nodes.new('CompositorNodeSeparateColor')
                dilate_red = nodes.new('CompositorNodeDilateErode')
                dilate_red.inputs["Type"].default_value = 'Distance'
                dilate_red.inputs["Size"].default_value = dilation
                dilate_green = nodes.new('CompositorNodeDilateErode')
                dilate_green.inputs["Type"].default_value = 'Distance'
                dilate_green.inputs["Size"].default_value = dilation
                dilate_blue = nodes.new('CompositorNodeDilateErode')
                dilate_blue.inputs["Type"].default_value = 'Distance'
                dilate_blue.inputs["Size"].default_value = dilation
                combine_color = nodes.new('CompositorNodeCombineColor')
                alpha_over = nodes.new('CompositorNodeAlphaOver')
                file_output = nodes.new('CompositorNodeOutputFile')
                file_output.format.media_type ='IMAGE'
                file_output.file_name = ""
                file_output.file_output_items.new('RGBA', 'Image1')
                file_output.file_output_items.new('RGBA', 'Image2')
                temp_path = os.path.join(path, "speedtree_texture_bl_temp")
                try: 
                    os.makedirs(temp_path)
                except:
                    rmtree(temp_path)
                    os.makedirs(temp_path)
                file_output.directory = temp_path
                
                links.new(render_node.outputs['Diffuse Color'], diff_adjust.inputs['Image'])
                links.new(diff_adjust.outputs['Image'], set_alpha.inputs['Image'])
                links.new(render_node.outputs['Alpha'], set_alpha.inputs['Alpha'])
                links.new(diff_adjust.outputs['Image'], separate_color.inputs['Image'])
                links.new(separate_color.outputs['Red'], dilate_red.inputs['Mask'])
                links.new(separate_color.outputs['Green'], dilate_green.inputs['Mask'])
                links.new(separate_color.outputs['Blue'], dilate_blue.inputs['Mask'])
                links.new(dilate_red.outputs['Mask'], combine_color.inputs['Red'])
                links.new(dilate_green.outputs['Mask'], combine_color.inputs['Green'])
                links.new(dilate_blue.outputs['Mask'], combine_color.inputs['Blue'])
                links.new(combine_color.outputs['Image'], alpha_over.inputs["Background"])
                links.new(set_alpha.outputs['Image'], alpha_over.inputs["Foreground"])
                links.new(alpha_over.outputs['Image'], file_output.inputs[0])
                links.new(render_node.outputs['Alpha'], file_output.inputs[1])
                
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
                
                # Add Sun
                bpy.ops.object.light_add(type='SUN')
                sun = bpy.context.active_object
                sun.data.angle = radians(180) # Adjust Here
                
                # First Renders - Diffuse + Alpha
                cameras = []
                stored_uvs = []
                rotations = []
                for i,_ in enumerate(old_mats):
                    old_mats[i] = old_mats[i].copy()
                    old_mats[i].use_transparent_shadow = False
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
                            resolution_x = round(uv_y_diff * resolution)
                            resolution_y = round(uv_x_diff * resolution)
                            temp_scene.render.resolution_x = resolution_x
                            temp_scene.render.resolution_y = resolution_y
                        else:
                            uvs[0] = [uv_x_min, uv_y_min]
                            uvs[1] = [uv_x_max, uv_y_min]
                            uvs[2] = [uv_x_max, uv_y_max]
                            uvs[3] = [uv_x_min, uv_y_max]
                            uv_array = uvs[[0,1,2,2,3,0]].flatten()
                            mesh.attributes["DiffuseUV"].data.foreach_set("vector", uv_array)
                            resolution_x = round(uv_x_diff * resolution)
                            resolution_y = round(uv_y_diff * resolution)
                            temp_scene.render.resolution_x = resolution_x
                            temp_scene.render.resolution_y = resolution_y
                    
                    # Place Cameras
                    dim_max = np.max(billboard_dimensions)
                    if i == number_billboards - 1 and horiz_objects:
                        loc.length = dim_max * 2 + origin_z
                        bpy.ops.object.camera_add(location = loc, rotation = [0, 0, 0])
                    else:
                        loc.length = dim_max * 2
                        loc[2] = loc_z
                        bpy.ops.object.camera_add(location = loc, rotation = [np.pi*0.5, 0, rotation])
                    cam = bpy.context.active_object
                    cameras.append(cam)
                    cam.data.type = 'ORTHO'
                    cam.data.ortho_scale = dim_max
                    temp_scene.camera = cam
                    
                    # Render
                    file_output.file_output_items[0].name = "temp_diffuse_" + str(i)
                    file_output.file_output_items[1].name = "temp_alpha_" + str(i)
                    bpy.ops.render.render(scene = temp_scene.name)
                    
                # Second Renders - Ambient
                file_output.file_output_items.remove(file_output.file_output_items[1])
                for mat in old_mats:
                    mat_tree = mat.node_tree
                    mat_nodes = mat_tree.nodes
                    mat_tree.links.new(mat_nodes['Ambient Color'].outputs['Color'], mat_nodes['Specular BSDF'].inputs['Base Color'])
                
                # Remove diffuse adjustment  
                diff_adjust.inputs["Value"].default_value = 1 # Adjust Here
                
                #Render
                for i, cam in enumerate(cameras):
                    temp_scene.camera = cam
                    file_output.file_output_items[0].name = "temp_ambient_" + str(i)
                    bpy.ops.render.render(scene = temp_scene.name)
                    
                # Third Renders - Normals
                for j, mat in enumerate(old_mats):
                    # Deal with Matcap Material
                    matcap = bpy.data.materials["NORMAL_MATCAP_DIRECT_X_TWOSIDED_TEMPLATE"].copy()
                    matcap.name = "NORMAL_MATCAP_DIRECT_X_TWOSIDED"
                    matcap_ntree = matcap.node_tree
                    matcap_links = matcap_ntree.links
                    matcap_nodes = matcap_ntree.nodes
                    if mat["EBranchSeamSmoothing"] == 'OFF':
                        matcap_nodes['Control Branch Seam Smoothing'].inputs[1].default_value = 1  
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
                        if mat["EDetailLayer"] == 'OFF':
                            matcap_nodes['Control Normal Detail Layer'].inputs[1].default_value = 1
                    old_mats[j] = matcap
                
                #Render
                #temp_scene.view_settings.view_transform = 'Standard'
                for i, cam in enumerate(cameras):
                    temp_scene.camera = cam
                    file_output.file_output_items[0].name = "temp_normal_" + str(i)
                    bpy.ops.render.render(scene = temp_scene.name)
                    
                # Fourth Renders - Shadows
                for j, mat in enumerate(old_mats_backup):
                    # Restore original materials to benefit from transmission for mesh-based shadows
                    old_mats[j] = mat
                    
                # Shadow Method
                sun.data.angle = radians(30) # Adjust Here
                volume_geo_nodes = bpy.data.node_groups['Volume_Mesh_Template'].copy()
                volume_geo_nodes.name = "Volume_Mesh"
                temp_mesh.modifiers['Leaf_Card'].node_group = volume_geo_nodes
                temp_mesh.modifiers['Leaf_Card']['Socket_0'] = True
                temp_mesh.modifiers['Leaf_Card']['Socket_1'] = int(shadows_method)
                
                #Add shadow smoothing
                dilate_shadows = nodes.new('CompositorNodeDilateErode')
                dilate_shadows.inputs["Type"].default_value = 'Feather'
                min_res = min(resolution_x, resolution_y)
                dilate_shadows.inputs["Size"].default_value = -round(min_res * 0.04) # Adjust Here
                dilate_shadows.inputs["Falloff"].default_value = 'Sphere'
                contrast_shadows = nodes.new('CompositorNodeBrightContrast')
                contrast_shadows.inputs['Contrast'].default_value = -10 # Adjust Here
                blur_shadows = nodes.new('CompositorNodeBlur')
                blur_shadows.inputs["Type"].default_value = 'Gaussian'
                blur_size = min_res * 0.15 # Adjust Here
                blur_shadows.inputs["Size"].default_value[0] = blur_size
                blur_shadows.inputs["Size"].default_value[1] = blur_size
                links.new(render_node.outputs['Shadow'], dilate_shadows.inputs['Mask'])
                links.new(dilate_shadows.outputs['Mask'], contrast_shadows.inputs['Image'])
                links.new(contrast_shadows.outputs['Image'], blur_shadows.inputs['Image'])
                links.new(blur_shadows.outputs['Image'], file_output.inputs[0])
                
                #Render
                for i, cam in enumerate(cameras):
                    temp_scene.camera = cam
                    file_output.file_output_items[0].name = "temp_shadows_" + str(i)
                    bpy.ops.render.render(scene = temp_scene.name)
                    
                # Assemble the Textures
                temp_bg = bpy.data.images.new("Untitled", resolution, resolution)
                bg = nodes.new('CompositorNodeImage')
                bg.image = temp_bg
                for i in range(len(cameras)):
                    rgb = nodes.new('CompositorNodeImage')
                    rgb.image = bpy.data.images.load(glob(temp_path + "\\temp_diffuse_" + str(i) + "*.png")[0], check_existing = True)
                    shadows = nodes.new('CompositorNodeImage')
                    shadows.image = bpy.data.images.load(glob(temp_path + "\\temp_shadows_" + str(i) + "*.png")[0], check_existing = True)
                    mix_shadows = nodes.new('ShaderNodeMix')
                    mix_shadows.data_type = 'RGBA'
                    mix_shadows.blend_type = 'MULTIPLY'
                    mix_shadows.inputs['Factor'].default_value = 0.85 # Adjust Here
                    transform_rgb = nodes.new('CompositorNodeTransform')
                    transform_rgb.inputs['X'].default_value = (((stored_uvs[i][0] + stored_uvs[i][1]) * 0.5) - 0.5) * resolution
                    transform_rgb.inputs['Y'].default_value = (((stored_uvs[i][2] + stored_uvs[i][3]) * 0.5) - 0.5) * resolution
                    transform_rgb.inputs['Angle'].default_value = rotations[i]
                    alpha_over_rgb = nodes.new('CompositorNodeAlphaOver')
                    alpha = nodes.new('CompositorNodeImage')
                    alpha.image = bpy.data.images.load(glob(temp_path + "\\temp_alpha_" + str(i) + "*.png")[0], check_existing = True)
                    transform_alpha = nodes.new('CompositorNodeTransform')
                    transform_alpha.inputs['X'].default_value = (((stored_uvs[i][0] + stored_uvs[i][1]) * 0.5) - 0.5) * resolution
                    transform_alpha.inputs['Y'].default_value = (((stored_uvs[i][2] + stored_uvs[i][3]) * 0.5) - 0.5) * resolution
                    transform_alpha.inputs['Angle'].default_value = rotations[i]
                    alpha_over_alpha = nodes.new('CompositorNodeAlphaOver')
                    normal = nodes.new('CompositorNodeImage')
                    normal.image = bpy.data.images.load(glob(temp_path + "\\temp_normal_" + str(i) + "*.png")[0], check_existing = True)
                    transform_normal = nodes.new('CompositorNodeTransform')
                    transform_normal.inputs['X'].default_value = (((stored_uvs[i][0] + stored_uvs[i][1]) * 0.5) - 0.5) * resolution
                    transform_normal.inputs['Y'].default_value = (((stored_uvs[i][2] + stored_uvs[i][3]) * 0.5) - 0.5) * resolution
                    transform_normal.inputs['Angle'].default_value = rotations[i]
                    alpha_over_normal = nodes.new('CompositorNodeAlphaOver')
                    ambient = nodes.new('CompositorNodeImage')
                    ambient.image = bpy.data.images.load(glob(temp_path + "\\temp_ambient_" + str(i) + "*.png")[0], check_existing = True)
                    transform_ambient = nodes.new('CompositorNodeTransform')
                    transform_ambient.inputs['X'].default_value = (((stored_uvs[i][0] + stored_uvs[i][1]) * 0.5) - 0.5) * resolution
                    transform_ambient.inputs['Y'].default_value = (((stored_uvs[i][2] + stored_uvs[i][3]) * 0.5) - 0.5) * resolution
                    transform_ambient.inputs['Angle'].default_value = rotations[i]
                    alpha_over_ambient = nodes.new('CompositorNodeAlphaOver')
                    
                    links.new(rgb.outputs['Image'], mix_shadows.inputs[6])
                    links.new(shadows.outputs['Image'], mix_shadows.inputs[7])
                    links.new(mix_shadows.outputs['Result'], transform_rgb.inputs['Image'])
                    links.new(alpha.outputs['Image'], transform_alpha.inputs['Image'])
                    links.new(normal.outputs['Image'], transform_normal.inputs['Image'])
                    links.new(ambient.outputs['Image'], transform_ambient.inputs['Image'])
                    links.new(transform_rgb.outputs['Image'], alpha_over_rgb.inputs["Foreground"])
                    links.new(transform_alpha.outputs['Image'], alpha_over_alpha.inputs["Foreground"])
                    links.new(transform_normal.outputs['Image'], alpha_over_normal.inputs["Foreground"])
                    links.new(transform_ambient.outputs['Image'], alpha_over_ambient.inputs["Foreground"])
                    if not i:
                        links.new(bg.outputs['Image'], alpha_over_rgb.inputs["Background"])
                        links.new(bg.outputs['Image'], alpha_over_alpha.inputs["Background"])
                        links.new(bg.outputs['Image'], alpha_over_normal.inputs["Background"])
                        links.new(bg.outputs['Image'], alpha_over_ambient.inputs["Background"])
                    else:
                        links.new(alpha_over_previous_rgb.outputs['Image'], alpha_over_rgb.inputs["Background"])
                        links.new(alpha_over_previous_alpha.outputs['Image'], alpha_over_alpha.inputs["Background"])
                        links.new(alpha_over_previous_normal.outputs['Image'], alpha_over_normal.inputs["Background"])
                        links.new(alpha_over_previous_ambient.outputs['Image'], alpha_over_ambient.inputs["Background"])
                    alpha_over_previous_rgb = alpha_over_rgb
                    alpha_over_previous_alpha = alpha_over_alpha
                    alpha_over_previous_normal = alpha_over_normal
                    alpha_over_previous_ambient = alpha_over_ambient
                
                ramp_alpha = nodes.new('ShaderNodeValToRGB')
                ramp_alpha.color_ramp.elements[0].position = 0.149999 # Adjust Here
                ramp_alpha.color_ramp.elements[1].position = 0.15 # Adjust Here
                set_alpha_diffuse = nodes.new('CompositorNodeSetAlpha')
                set_alpha_diffuse.inputs["Type"].default_value = 'Replace Alpha'
                set_alpha_normal = nodes.new('CompositorNodeSetAlpha')
                #set_alpha_normal.inputs["Type"].default_value = 'Replace Alpha'
                file_output.directory = path
                file_output.format.file_format = file_format
                file_output.file_output_items[0].name = "temp_billboard_bl"
                file_output.file_output_items.new('RGBA', 'temp_billboard_bl_n')
                
                links.new(alpha_over_rgb.outputs['Image'], set_alpha_diffuse.inputs[0])
                links.new(alpha_over_alpha.outputs['Image'], ramp_alpha.inputs['Fac'])
                links.new(ramp_alpha.outputs['Color'], set_alpha_diffuse.inputs[1])
                links.new(alpha_over_normal.outputs['Image'], set_alpha_normal.inputs[0])
                links.new(alpha_over_ambient.outputs['Image'], set_alpha_normal.inputs[1])
                links.new(set_alpha_diffuse.outputs['Image'], file_output.inputs[0])
                links.new(set_alpha_normal.outputs['Image'], file_output.inputs[1])
                
                # Render
                bpy.ops.render.render(scene = temp_scene.name)
                
                # Rename the files
                old_path_diff = glob(path+"\\temp_billboard_bl*"+ext)[0]
                old_path_normal = glob(path+"\\temp_billboard_bl_n*"+ext)[0]
                new_path_diff = path + filename
                new_path_normal = path + filename_normal
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
                        billboard_mat["diffuseTexture"] = new_path_diff
                        image_normal = load_dds(new_path_normal)
                        image_normal.name += ".dds"
                        image_normal.filepath = new_path_normal
                        image_normal.colorspace_settings.name = 'Non-Color'
                        billboard_mat_nodes["Normal Texture"].image = image_normal
                        billboard_mat_nodes["Branch Seam Normal Texture"].image = image_normal
                        billboard_mat["normalTexture"] = new_path_normal
                    else:
                        image = bpy.data.images.load(new_path_diff)
                        image.colorspace_settings.name = 'sRGB'
                        billboard_mat_nodes["Diffuse Texture"].image = image
                        billboard_mat_nodes["Branch Seam Diffuse Texture"].image = image
                        billboard_mat["diffuseTexture"] = new_path_diff
                        image_normal = bpy.data.images.load(new_path_normal)
                        image_normal.colorspace_settings.name = 'Non-Color'
                        billboard_mat_nodes["Normal Texture"].image = image_normal
                        billboard_mat_nodes["Branch Seam Normal Texture"].image = image_normal
                        billboard_mat["normalTexture"] = new_path_normal
                
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