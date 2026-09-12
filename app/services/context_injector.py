"""Context Injector for prompt engineering with reference tagging and engine routing."""

ACTION_KEYWORDS = {"dash", "dodge", "fight", "strike", "slash", "combat", "kick", "punch", "jump", "run"}
ATMOSPHERIC_KEYWORDS = {"stare", "speak", "sunset", "stand", "walk", "sit", "look", "gaze", "breathe"}
NEGATIVE_PROMPT = "2d anime, cartoon, plastic skin, deformed scar, missing eye scar, altered cape color, extra fingers, distorted sword, face morphing between frames, 60fps video look"
GLOBAL_STYLE = "photorealistic skin texture, cinematic 35mm lens, moody sunset lighting, 24fps film grain, 4k resolution"


class ContextInjector:
    """Handles prompt injection with reference tagging, locked traits, and engine routing."""

    def inject_locked_traits(self, prompt: str, traits: list[str]) -> str:
        """Inject locked traits into the prompt."""
        if not traits:
            return prompt
        traits_str = ", ".join(traits)
        return f"{prompt} [{traits_str}]"

    def get_negative_prompt(self) -> str:
        """Return the negative prompt for image generation."""
        return NEGATIVE_PROMPT

    def get_global_style(self) -> str:
        """Return the global style appendage."""
        return GLOBAL_STYLE

    def detect_engine(self, prompt: str) -> str:
        """Detect the appropriate engine based on prompt keywords."""
        words = set(prompt.lower().split())
        if words & ACTION_KEYWORDS:
            return "SEEDANCE"
        if words & ATMOSPHERIC_KEYWORDS:
            return "FLOW"
        return "SEEDANCE"

    def inject_reference_tag(self, prompt: str, ref_image: str, ip_adapter_scale: float = 0.85) -> str:
        """Inject a reference image tag into the prompt."""
        return f"{prompt} [INPUT_REF: {ref_image}, ip_adapter_scale={ip_adapter_scale}]"

    def inject_global_style(self, prompt: str) -> str:
        """Append global style to the prompt."""
        return f"{prompt} {GLOBAL_STYLE}"

    def build_full_prompt(
        self,
        prompt: str,
        locked_traits: list[str] | None = None,
        ref_image: str | None = None,
        ip_adapter_scale: float = 0.85,
        include_style: bool = True,
    ) -> str:
        """Build a full prompt with all context injections."""
        result = prompt
        if locked_traits:
            result = self.inject_locked_traits(result, locked_traits)
        if ref_image:
            result = self.inject_reference_tag(result, ref_image, ip_adapter_scale)
        if include_style:
            result = self.inject_global_style(result)
        return result

    def get_motion_scale(self, engine: str) -> float:
        """Get the motion scale for the given engine."""
        if engine == "SEEDANCE":
            return 1.4
        if engine == "FLOW":
            return 0.8
        return 1.0