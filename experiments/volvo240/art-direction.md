Current targeted refinement: controlled polygonal wheel openings, tight connected
reveals and restrained panel shading; 6162 triangles. The latest Blender master
and GLB pass technical gates; appearance approval remains pending. See
refinement/assessment.md. Earlier checkpoint notes below are historical.

# Art direction and review access

Stylized realism within Vrigstad Joyride's visual identity. Recognizable Volvo
240 silhouette and correct real-world proportions come first; clean continuous
geometry and restrained triangle counts come next. Simplify small details,
materials and reflections. Do not pursue photographic paint, complex chrome,
roughness textures or showroom lighting that would clash with the village.

The current 3,748-triangle clay checkpoint still needs primary-form and geometry
work. Color treatment does not change its rejection. No cosmetic details or
additional geometry correction cycles were added for the viewer task.

All generation, Blender rendering, checks, packaging and exports execute in the
Codex environment. Viewers need only Safari (or another WebGL-capable browser).
They do not need Blender, a terminal, Python, npm, or any local software setup.
The reproducibility commands in README.md are for Codex/maintainers.

The extended `media/vehicles/preview.html` preserves exact authored scale and
-Z-forward orientation for the experimental GLB. Existing Kenney candidates keep
their previous uniform review scale and rotation. Camera framing does not stretch
vehicles. Front/side/rear/top are orthographic; three-quarter is perspective.
Touch interaction supports one-finger rotation and two-finger pinch, with
buttons as alternatives. PNG sheets remain accessible when WebGL is unavailable.

Joyride film mode loads the existing `src/visual/film-pipeline.js` unchanged,
including its photographic creative transform and ACES exposure. Preview-only
settings lower grain and disable mist for clear geometric inspection. Materials
are matte, nonmetallic and have no environment reflection map. Neutral clay mode
removes the creative grade and grain. No game lighting, colors or assets change.

Hosting uses a separate, private review Site with static assets. The same static
package is GitHub Pages compatible and has no backend, CDN dependency or app
integration. Publishing the review is not game integration or visual approval.
