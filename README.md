# Blender_SRT_Addon
## Content of the addon
An addon made to import, create, edit and export .srt meshes (Real Time SpeedTree Meshes) in Blender, for free. Developed for Blender 4.1.1, other versions are not tested.

The main features are:
- Supports all geometry types except rigid meshes.
- Supports SpeedTree LOD system parameters.
- Supports most of Speedtree shader's parameters.
- Can generate billboard textures with a single click.

You can find all the required tools in a SpeedTree side panel of the 3D view.

![addon_viewport](https://imgur.com/h8APXiI.png)

## Recommendations

- The addon is able to leverage the [DDS Addon](https://github.com/matyalatte/Blender-DDS-Addon/releases). When this dds addon is installed, the .srt importer will automatically use it to open .dds files if needed. Moreover, when installed, it offers the possibility to create billboard textures as .dds directly from the SpeedTree side panel.

## Limitations

- The addon doesn't support wind,
- The addon is meant for SpeedTree v7 assets. Earlier .srt versions may not work properly and later speedtree versions don't support .srt format at all,
- The .srt export is specifically designed towards the engines with the "UNIFIED_SHADERS" used by REDEngine (The Witcher 3). Other engines such as Unreal Engine may or may not be able to read the files exported by this addon,
- A couple specificities of that game shader is that rigid meshes and horizontal billboards are not supported. Thus, these are currently not exported by the .srt exporter,
- The blender shader only works with EEVEE renderer and it looks best with a hand-crafted lighting rather than a hdri,
- Colors are expected to differ from in-game visuals as the shader I built in Blender is not a 1:1 reproduction,

## Documentation

Some general documentation about SpeedTree can be found [here](https://docs.speedtree.com/doku.php?id=start).

Video demonstration of the various tools present in the side panel of the addon (old version):
[![SpeedTree Addon Video](https://i.ytimg.com/vi/9nWWpDncmZg/maxresdefault.jpg)](https://www.youtube.com/watch?v=9nWWpDncmZg)

This project was initially developed to mod Witcher 3's vegetation, but it might be useful for other purposes as well.

Copyright (c) 2021 Ard Carraigh

This project is licensed under the terms of the Creative Commons Attribution-NonCommercial 4.0 International Public License.
