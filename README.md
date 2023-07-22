# Blender_SRT_Addon
## Content of the addon
An addon made to import, create, edit and export .srt meshes (Real Time SpeedTree Meshes) in Blender, for free. Developed for Blender 3.6.1, other versions are not tested.

The main features are
- Supports all geometry types except rigid meshes.
- Supports SpeedTree LOD system parameters.
- Supports most of Speedtree shader's parameters.
- Can generate billboard textures with a single click.

You can find all the required tools in a SpeedTree side panel of the 3D view.

![addon_viewport](https://imgur.com/h8APXiI.png)

## Recommendations

- In order to obtain a .json dump from a .srt, you must install [Wolvenkit 7](https://github.com/WolvenKit/WolvenKit-7/releases)
- For the addon to automatically read and write .srt files, you must add the path to WolvenKit's CLI.exe in the addon preferences
![addon_preferences](https://imgur.com/WFjB5sP.png)
- The addon is able to leverage the [DDS Addon](https://github.com/matyalatte/Blender-DDS-Addon/releases). When this dds addon is installed, the .srt importer will automatically use it to open .dds files if needed. Moreover, when installed, it offers the possibility to create billboard textures as .dds directly from the SpeedTree side panel

## Documentation

Some general documentation about SpeedTree can be found [here](https://docs.speedtree.com/doku.php?id=start)

Video demonstration of the various tools present in the side panel of the addon (old version):
[![SpeedTree Addon Video](https://i.ytimg.com/vi/9nWWpDncmZg/maxresdefault.jpg)](https://www.youtube.com/watch?v=9nWWpDncmZg)

This project was initially developed to mod Witcher 3's vegetation, but it might be useful for other purposes as well.

Copyright (c) 2021 Ard Carraigh

This project is licensed under the terms of the Creative Commons Attribution-NonCommercial 4.0 International Public License.
