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
                
                # Prepare last LOD Collection
                last_lod_col = lods_coll[-1]
                last_lod_col_name = last_lod_col.name
                last_lod_col_dot = last_lod_col_name.find(".")
                if last_lod_col_dot > -1:
                    last_lod_col_number = int(last_lod_col_name[last_lod_col_dot + 1:])
                else:
                    last_lod_col_number = 0
                JoinThem(last_lod_col.objects)
                last_lod_mesh = last_lod_col.objects[0]
                last_lod_modif = last_lod_mesh.modifiers['Leaf_Card']
                
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
                bpy.context.view_layer.use_pass_shadow = True
                active_scene = bpy.context.scene
                active_scene.view_settings.view_transform = 'Standard'
                active_scene.render.film_transparent = True
                active_scene.render.engine = 'BLENDER_EEVEE'
                active_scene.use_nodes = True
                ntree = active_scene.node_tree
                nodes = ntree.nodes
                links = ntree.links
                composite = nodes["Composite"]
                mask = nodes.new('CompositorNodeMask')
                mask.size_source = 'FIXED'
                mask.size_x = resolution
                mask.size_y = resolution
                key = nodes.new('CompositorNodeColorMatte')
                key.inputs['Key Color'].default_value = (0,0,0,0)
                viewer = nodes.new('CompositorNodeViewer')
                file_output = nodes.new('CompositorNodeOutputFile')
                file_output.format.file_format = file_format
                file_output.file_slots.new('Image2')
                if use_custom_path and custom_path:
                    file_output.base_path = custom_path
                else:
                    file_output.base_path = path
                links.new(mask.outputs['Mask'], key.inputs['Image'])
                
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
                            uv_array = uvs[[1,0,3,3,2,1]].flatten()
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
                    
                    # Make Another New Scene for Volume Mesh (shadows)
                    scene_shadows = active_scene.copy()
                    scenes.append(scene_shadows)
                    bpy.context.window.scene = scene_shadows 
                    view_layer_shadows = bpy.context.view_layer
                    view_layer_shadows.name = "ViewLayerShadows" + str(i+1)
                    view_layers.append(view_layer_shadows)
                    
                    # Place Cameras
                    if i == number_billboards - 1 and horiz_objects:
                        loc.length = billboard_dimensions[0] * 0.75 + origin_z
                        bpy.ops.object.camera_add(location = loc, rotation = [0, 0, 0])
                    else:
                        loc.length = billboard_dimensions[0] * 0.75
                        loc[2] = loc_z
                        bpy.ops.object.camera_add(location = loc, rotation = [np.pi*0.5, 0, rotation])
                    cam = bpy.context.active_object
                    cameras.append(cam)
                    cam.data.type = 'ORTHO'
                    cam.data.ortho_scale = np.max(billboard_dimensions)
                    scene.camera = cam
                    scene_shadows.camera = cam
                    
                    # Make a New Collection for Each Billboard (Necessary for Facing Leaves...)
                    last_lod_col_number += 1
                    new_coll = GetCollection("LOD" + str(len(lods_coll) - 1) + str(last_lod_col_number * 0.001)[2:], True, False)
                    collections.append(new_coll)
                    selectOnly(last_lod_mesh)
                    bpy.ops.object.duplicate(linked=False, mode='TRANSLATION')
                    new_mesh = bpy.context.active_object
                    meshes.append(new_mesh)
                    new_coll.objects.link(new_mesh)
                    last_lod_col.objects.unlink(new_mesh)
                    new_geom_nodes = last_lod_modif.node_group.copy()
                    geom_nodes.append(new_geom_nodes)
                    new_mesh.modifiers['Leaf_Card'].node_group = new_geom_nodes
                    new_mesh.modifiers['Leaf_Card'].node_group.nodes['Camera'].inputs['Object'].default_value = cam
                    
                    # Make a New Collection for a Volume Mesh for Each Billboard (Trick for Better Shadows)
                    new_coll_shadows = GetCollection("LOD" + str(len(lods_coll) - 1) + str(last_lod_col_number * 0.001)[2:] + "Shadows", True, False)
                    collections.append(new_coll_shadows)
                    bpy.ops.object.duplicate(linked=False, mode='TRANSLATION')
                    new_mesh_shadows = bpy.context.active_object
                    meshes.append(new_mesh_shadows)
                    new_coll_shadows.objects.link(new_mesh_shadows)
                    new_coll.objects.unlink(new_mesh_shadows)
                    bpy.ops.object.modifier_apply(modifier='Leaf_Card')
                    new_geom_nodes_shadows = bpy.data.node_groups["Volume_Mesh_Template"].copy()
                    new_geom_nodes_shadows.name = "Volume_Mesh"
                    modif_shadows = new_mesh_shadows.modifiers.new(type='NODES', name = "Volume_Mesh")
                    modif_shadows.node_group = new_geom_nodes_shadows
                    bpy.ops.object.modifier_apply(modifier="Volume_Mesh")
                    while len(new_mesh_shadows.data.materials):
                        new_mesh_shadows.data.materials.pop()
                    
                    # Make the compositing
                    mix_shadows = nodes.new('CompositorNodeMixRGB')
                    mix_shadows.blend_type = 'MULTIPLY'
                    mix_shadows.inputs['Fac'].default_value = 0.6
                    erode_shadows = nodes.new('CompositorNodeDilateErode')
                    erode_shadows.mode = 'FEATHER'
                    erode_shadows.distance = -5
                    shadows_aa = nodes.new('CompositorNodeAntiAliasing')
                    shadows_aa.threshold = 0
                    reroute_alpha = nodes.new('NodeReroute')
                    color_ramp = nodes.new('CompositorNodeValToRGB')
                    color_ramp.color_ramp.elements[0].position = 0.49999995
                    color_ramp.color_ramp.elements[1].position = 0.49999996
                    #Dilation
                    erode_alpha = nodes.new('CompositorNodeDilateErode')
                    erode_alpha.mode = 'DISTANCE'
                    erode_alpha.distance = -1
                    subtract = nodes.new('CompositorNodeMath')
                    subtract.operation = 'SUBTRACT'
                    set_alpha_outline = nodes.new('CompositorNodeSetAlpha')
                    separate_outline = nodes.new('CompositorNodeSeparateColor')
                    dilate_red = nodes.new('CompositorNodeDilateErode')
                    dilate_red.mode = 'DISTANCE'
                    dilate_red.distance = dilation
                    dilate_green = nodes.new('CompositorNodeDilateErode')
                    dilate_green.mode = 'DISTANCE'
                    dilate_green.distance = dilation
                    dilate_blue = nodes.new('CompositorNodeDilateErode')
                    dilate_blue.mode = 'DISTANCE'
                    dilate_blue.distance = dilation
                    combine_dilated = nodes.new('CompositorNodeCombineColor')
                    set_alpha_pre = nodes.new('CompositorNodeSetAlpha')
                    set_alpha_pre.mode = 'REPLACE_ALPHA'
                    alpha_over_pre = nodes.new('CompositorNodeAlphaOver')
                    #Transform
                    set_alpha = nodes.new('CompositorNodeSetAlpha')
                    set_alpha.mode = 'REPLACE_ALPHA'
                    transform = nodes.new('CompositorNodeTransform')
                    transform.inputs['X'].default_value = (((uv_x_max + uv_x_min) * 0.5) - 0.5) * resolution
                    transform.inputs['Y'].default_value = (((uv_y_max + uv_y_min) * 0.5) - 0.5) * resolution
                    transform.inputs['Angle'].default_value = render_rotation
                    alpha_over = nodes.new('CompositorNodeAlphaOver')
                    #Links
                    links.new(reroute_alpha.outputs['Output'], color_ramp.inputs['Fac'])
                    links.new(reroute_alpha.outputs['Output'], set_alpha_pre.inputs['Alpha'])
                    links.new(erode_shadows.outputs['Mask'], shadows_aa.inputs['Image'])
                    links.new(shadows_aa.outputs['Image'], mix_shadows.inputs[2])
                    links.new(mix_shadows.outputs['Image'], set_alpha_pre.inputs['Image'])
                    links.new(mix_shadows.outputs['Image'], set_alpha_outline.inputs['Image'])
                    links.new(color_ramp.outputs['Image'], erode_alpha.inputs['Mask'])
                    links.new(erode_alpha.outputs['Mask'], subtract.inputs[1])
                    links.new(color_ramp.outputs['Image'], subtract.inputs[0])
                    links.new(subtract.outputs['Value'], set_alpha_outline.inputs['Alpha'])
                    links.new(set_alpha_outline.outputs['Image'], separate_outline.inputs['Image'])
                    links.new(separate_outline.outputs['Red'], dilate_red.inputs['Mask'])
                    links.new(separate_outline.outputs['Green'], dilate_green.inputs['Mask'])
                    links.new(separate_outline.outputs['Blue'], dilate_blue.inputs['Mask'])
                    links.new(separate_outline.outputs['Alpha'], combine_dilated.inputs['Alpha'])
                    links.new(dilate_red.outputs['Mask'], combine_dilated.inputs['Red'])
                    links.new(dilate_green.outputs['Mask'], combine_dilated.inputs['Green'])
                    links.new(dilate_blue.outputs['Mask'], combine_dilated.inputs['Blue'])
                    links.new(combine_dilated.outputs['Image'], alpha_over_pre.inputs[1])
                    links.new(set_alpha_pre.outputs['Image'], alpha_over_pre.inputs[2])
                    links.new(alpha_over_pre.outputs['Image'], set_alpha.inputs['Image'])
                    links.new(color_ramp.outputs['Image'], set_alpha.inputs['Alpha'])
                    links.new(set_alpha.outputs['Image'], transform.inputs['Image'])
                    links.new(transform.outputs['Image'], alpha_over.inputs[2])
                        
                    # Render nodes
                    if not i:
                        nodes['Render Layers'].scene = scene
                        nodes['Render Layers'].layer = view_layer.name
                        render_node_shadows = nodes.new('CompositorNodeRLayers')
                        render_node_shadows.scene = scene_shadows
                        render_node_shadows.layer = view_layer_shadows.name
                        links.new(key.outputs['Image'], alpha_over.inputs[1])
                        links.new(nodes['Render Layers'].outputs['DiffCol'], mix_shadows.inputs[1])
                        links.new(nodes['Render Layers'].outputs['Alpha'], reroute_alpha.inputs['Input'])
                        links.new(render_node_shadows.outputs['Shadow'], erode_shadows.inputs['Mask'])
                    else:
                        render_node = nodes.new('CompositorNodeRLayers')
                        render_node.scene = scene
                        render_node.layer = view_layer.name
                        render_node_shadows = nodes.new('CompositorNodeRLayers')
                        render_node_shadows.scene = scene_shadows
                        render_node_shadows.layer = view_layer_shadows.name
                        links.new(alpha_over_previous.outputs['Image'], alpha_over.inputs[1])
                        links.new(render_node.outputs['DiffCol'], mix_shadows.inputs[1])
                        links.new(render_node.outputs['Alpha'], reroute_alpha.inputs['Input'])
                        links.new(render_node_shadows.outputs['Shadow'], erode_shadows.inputs['Mask'])
                    # File Output
                    if i == number_billboards - 1:
                        links.new(alpha_over.outputs['Image'], composite.inputs['Image'])
                        links.new(alpha_over.outputs['Image'], viewer.inputs['Image'])
                        links.new(alpha_over.outputs['Image'], file_output.inputs[0])
                        alpha_over_normal = nodes.new('CompositorNodeAlphaOver')
                        alpha_over_normal.inputs[1].default_value = (0.219525, 0.21586, 1, 1)
                        links.new(alpha_over.outputs['Image'], alpha_over_normal.inputs[2])
                        links.new(alpha_over_normal.outputs['Image'], file_output.inputs[1])
                        # Make a last unused camera and render otherwise the last render doesn't show up for some reason
                        scene = active_scene.copy()
                        scenes.append(scene)
                        render_node = nodes.new('CompositorNodeRLayers')
                        render_node.scene = scene
                            
                    alpha_over_previous = alpha_over
                
                # Make a Diffuse Color Render for Each Billboard    
                for i,_ in enumerate(scenes):
                    if i != len(scenes) - 1:
                        bpy.context.window.scene = scenes[i]
                        for col in collections:
                            if collections[i] != col:
                                GetCollection(col.name, make_active = True)
                                bpy.context.view_layer.active_layer_collection.exclude = True
                    # Render
                    bpy.ops.render.render(scene = scenes[i].name)
                        
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
                for i,_ in enumerate(scenes):
                    if i != len(scenes) - 1:
                        old_mats = meshes[i].data.materials
                        if old_mats:
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
                                
                        else:
                            matcap = bpy.data.materials["NORMAL_MATCAP_DIRECT_X_TEMPLATE"].copy()
                            matcap.name = "NORMAL_MATCAP_DIRECT_X"
                            old_mats.append(matcap)
                    # Render
                    bpy.ops.render.render(scene = scenes[i].name)

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
                bpy.data.objects.remove(sun)
                for node in nodes:
                    if node != nodes["Composite"] and node != nodes['Render Layers']:
                        nodes.remove(node)
                for cam in cameras:
                    bpy.data.objects.remove(cam)
                for scene in scenes:
                    bpy.data.scenes.remove(scene)
                for col in collections: 
                    bpy.data.collections.remove(col)
                        
                # Purge orphan data left unused
                override = bpy.context.copy()
                override["area.type"] = ['OUTLINER']
                override["display_mode"] = ['ORPHAN_DATA']
                bpy.ops.outliner.orphans_purge(override)
                        
                GetCollection()
                                  
    return   