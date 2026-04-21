# Overlay: V2V Visual

- **Platform Priority:** Kling for V2V motion transfer, Runway for style transfer. Veo3 for text-to-video UGC only.
- **Anti-Melting:** Always include temporal anchors: fixed camera position for first 2s, gradual motion only. "Consistent subject identity" in every prompt.
- **Camera Physics:** Specify real-world camera parameters: focal length (35mm/50mm/85mm), dolly/pan/tilt, shake intensity 0-10. Never use abstract motion terms.
- **Temporal Consistency:** Reference frame 1 description in frame N. "Same person, same clothing, same lighting" as mandatory constraint.
- **Kling Constraints:** Duration 5-10s, aspect_ratio 9:16. Front-load subject description. Max prompt 500 chars. Negative: "morphing, melting, flickering, distortion".
- **Runway Constraints:** Use style reference image when available. "Cinematic, 24fps, shallow depth of field" as quality anchors. Max 1000 chars.
- **Prompt Structure:** [Subject Lock] + [Camera Motion] + [Temporal Anchor] + [Style] + [Negative Constraints]. Order matters.
- **QA Gate:** Every V2V render must pass visual_flywheel before publish. SSIM > 0.6 against reference, VLM score > 7/10.
- **KB Source:** V2V patterns from AI Video Bootcamp (AKOS domain: v2v_video). Update patterns after each new scrape.
- **Negative Prompts:** Always include: "no morphing, no melting, no flickering, no extra limbs, no distorted text, no impossible physics".
