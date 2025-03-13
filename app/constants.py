#!/usr/bin/env python3
# Copyright (c) 2023-present Craig P. Russo and CR2 Creative

"""
Constants module to prevent circular imports
"""

# App constants
APP_NAME = "CR2 Project Creator"
APP_VERSION = "0.08"
RECENT_PROJECTS_MAX = 5
RECENT_TEMPLATES_MAX = 5

# Default structures
DEFAULT_STRUCTURES = {
    "Video Editing - Basic": [
        {"footage": []},
        {"graphics": []},
        {"audio": []},
        {"exports": []},
        {"project_files": []}
    ],
    "Video Editing - Standard": [
        {"footage": [
            {"raw": []}, 
            {"transcoded": []}, 
            {"archives": []}
        ]},
        {"audio": [
            {"music": []}, 
            {"sfx": []}, 
            {"voice_over": []}, 
            {"stems": []}
        ]},
        {"graphics": [
            {"lower_thirds": []}, 
            {"titles": []}, 
            {"logos": []}, 
            {"backgrounds": []}
        ]},
        {"project_files": [
            {"premiere": []}, 
            {"after_effects": []}, 
            {"avid": []}
        ]},
        {"exports": [
            {"finals": []}, 
            {"previews": []}, 
            {"deliverables": []}
        ]},
        {"documents": [
            {"scripts": []}, 
            {"shot_lists": []}, 
            {"notes": []}
        ]},
        {"luts": []},
        {"assets": []}
    ],
    "Video Editing - Advanced": [
        {"footage": [
            {"raw": []}, 
            {"transcoded": []}, 
            {"archives": []}, 
            {"b_roll": []}, 
            {"interviews": []}
        ]},
        {"audio": [
            {"music": []}, 
            {"sfx": []}, 
            {"voice_over": []}, 
            {"stems": []}, 
            {"ambience": []}
        ]},
        {"graphics": [
            {"lower_thirds": []}, 
            {"titles": []}, 
            {"logos": []}, 
            {"backgrounds": []}, 
            {"animations": []}
        ]},
        {"project_files": [
            {"premiere": []}, 
            {"after_effects": []}, 
            {"davinci_resolve": []}
        ]},
        {"exports": [
            {"finals": []}, 
            {"client_review": []}, 
            {"social_media": []}, 
            {"broadcast": []}
        ]},
        {"documents": [
            {"scripts": []}, 
            {"shot_lists": []}, 
            {"notes": []}, 
            {"client_feedback": []}
        ]},
        {"luts": [
            {"technical": []}, 
            {"creative": []}
        ]},
        {"assets": [
            {"stock_footage": []}, 
            {"stock_music": []}, 
            {"fonts": []}
        ]}
    ],
    "Motion Graphics - Standard": [
        {"source_files": [
            {"illustrator": []}, 
            {"photoshop": []}, 
            {"c4d": []}, 
            {"blender": []}
        ]},
        {"assets": [
            {"textures": []}, 
            {"models": []}, 
            {"backgrounds": []}, 
            {"fonts": []}
        ]},
        {"renders": [
            {"previews": []}, 
            {"finals": []}, 
            {"elements": []}
        ]},
        {"audio": [
            {"music": []}, 
            {"sfx": []}
        ]},
        {"project_files": [
            {"after_effects": []}, 
            {"cinema4d": []}
        ]},
        {"reference": [
            {"inspiration": []}, 
            {"storyboards": []}
        ]},
        {"exports": []}
    ],
    "Motion Graphics - Advanced": [
        {"source_files": [
            {"illustrator": []}, 
            {"photoshop": []}, 
            {"c4d": []}, 
            {"blender": []}, 
            {"substance": []}
        ]},
        {"assets": [
            {"textures": []}, 
            {"models": []}, 
            {"backgrounds": []}, 
            {"fonts": []}, 
            {"hdri": []}
        ]},
        {"renders": [
            {"previews": []}, 
            {"finals": []}, 
            {"elements": []}, 
            {"passes": []}
        ]},
        {"audio": [
            {"music": []}, 
            {"sfx": []}, 
            {"voice_over": []}
        ]},
        {"project_files": [
            {"after_effects": []}, 
            {"cinema4d": []}, 
            {"houdini": []}
        ]},
        {"reference": [
            {"inspiration": []}, 
            {"storyboards": []}, 
            {"animatics": []}
        ]},
        {"client": [
            {"feedback": []}, 
            {"approvals": []}
        ]},
        {"exports": [
            {"web": []}, 
            {"broadcast": []}, 
            {"social_media": []}
        ]}
    ],
    "VFX - Standard": [
        {"footage": [
            {"plates": []}, 
            {"greenscreen": []}, 
            {"elements": []}
        ]},
        {"3d": [
            {"models": []}, 
            {"textures": []}, 
            {"hdri": []}, 
            {"alembic": []}
        ]},
        {"2d": [
            {"masks": []}, 
            {"mattes": []}, 
            {"backgrounds": []}
        ]},
        {"tracking": [
            {"camera_tracks": []}, 
            {"object_tracks": []}
        ]},
        {"renders": [
            {"passes": []}, 
            {"finals": []}, 
            {"elements": []}
        ]},
        {"project_files": [
            {"nuke": []}, 
            {"fusion": []}, 
            {"after_effects": []}
        ]},
        {"assets": []},
        {"exports": []}
    ],
    "VFX - Advanced": [
        {"footage": [
            {"plates": []}, 
            {"elements": []}, 
            {"reference": []}, 
            {"calibration": []}
        ]},
        {"3d": [
            {"models": []}, 
            {"textures": []}, 
            {"hdri": []}, 
            {"alembic": []}, 
            {"fbx": []}, 
            {"simulations": []}
        ]},
        {"2d": [
            {"masks": []}, 
            {"mattes": []}, 
            {"backgrounds": []}, 
            {"paint": []}, 
            {"grain": []}
        ]},
        {"tracking": [
            {"camera_tracks": []}, 
            {"object_tracks": []}, 
            {"roto": []}, 
            {"matchmove": []}
        ]},
        {"renders": [
            {"lighting_passes": []}, 
            {"cg_passes": []}, 
            {"composites": []}, 
            {"previews": []}, 
            {"finals": []}
        ]},
        {"project_files": [
            {"nuke": []}, 
            {"fusion": []}, 
            {"houdini": []}, 
            {"maya": []}, 
            {"blender": []}
        ]},
        {"assets": [
            {"stock_elements": []}, 
            {"practical_effects": []}
        ]},
        {"reference": [
            {"concept_art": []}, 
            {"previz": []}
        ]},
        {"client": [
            {"dailies": []}, 
            {"feedback": []}, 
            {"approvals": []}
        ]},
        {"exports": [
            {"delivery": []}, 
            {"shots": []}, 
            {"sequences": []}
        ]}
    ]
}

# Default template categories
DEFAULT_TEMPLATE_CATEGORIES = [
    "Video Editing",
    "Motion Graphics",
    "VFX",
    "Audio Production"
]

# Project types
PROJECT_TYPE_TO_STRUCTURE = {
    "Standard": "Video Editing - Standard",
    "Default": "Video Editing - Standard",
    "Video Editing": "Video Editing - Standard",
    "Motion Graphics": "Motion Graphics - Standard", 
    "Design": "Video Editing - Basic",
    "Audio": "Video Editing - Basic",
    "VFX": "VFX - Standard"
} 