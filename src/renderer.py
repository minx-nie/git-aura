"""
Git-Aura: SVG Renderer Module
Handles SVG generation, color mathematics, and visual effects.
"""

import numpy as np
import svgwrite
from svgwrite import Drawing
from svgwrite.container import Group
from typing import Optional
from dataclasses import dataclass


@dataclass
class ColorRGB:
    """RGB color representation with float components (0-1)."""
    r: float
    g: float
    b: float
    
    @classmethod
    def from_hex(cls, hex_color: str) -> "ColorRGB":
        """
        Create ColorRGB from hex string.
        
        Args:
            hex_color: Hex color like '#FF5733' or 'FF5733'.
            
        Returns:
            ColorRGB instance.
        """
        hex_color = hex_color.lstrip('#')
        if len(hex_color) != 6:
            # Default to gray if invalid
            return cls(0.5, 0.5, 0.5)
        
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return cls(r, g, b)
    
    def to_hex(self) -> str:
        """Convert to hex string."""
        r = int(np.clip(self.r * 255, 0, 255))
        g = int(np.clip(self.g * 255, 0, 255))
        b = int(np.clip(self.b * 255, 0, 255))
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def to_rgb_string(self, alpha: float = 1.0) -> str:
        """Convert to CSS rgba string."""
        r = int(np.clip(self.r * 255, 0, 255))
        g = int(np.clip(self.g * 255, 0, 255))
        b = int(np.clip(self.b * 255, 0, 255))
        return f"rgba({r},{g},{b},{alpha:.2f})"
    
    def blend(self, other: "ColorRGB", weight: float) -> "ColorRGB":
        """
        Blend with another color using linear interpolation.
        
        Args:
            other: Other color to blend with.
            weight: Weight for other color (0-1).
            
        Returns:
            Blended color.
        """
        return ColorRGB(
            r=self.r * (1 - weight) + other.r * weight,
            g=self.g * (1 - weight) + other.g * weight,
            b=self.b * (1 - weight) + other.b * weight
        )
    
    def lighten(self, amount: float) -> "ColorRGB":
        """Lighten color by blending with white."""
        white = ColorRGB(1.0, 1.0, 1.0)
        return self.blend(white, amount)
    
    def darken(self, amount: float) -> "ColorRGB":
        """Darken color by blending with black."""
        black = ColorRGB(0.0, 0.0, 0.0)
        return self.blend(black, amount)


class ColorPaletteGenerator:
    """
    Generates color palettes from language statistics.
    Uses weighted averaging in LAB color space for perceptually uniform blending.
    """
    
    # Dark mode friendly background
    BACKGROUND_COLOR = "#0d1117"
    
    # Fallback colors if no language data
    DEFAULT_COLORS = ["#58a6ff", "#8b5cf6", "#f97316"]
    
    def __init__(self, languages: list[dict]):
        """
        Initialize palette generator.
        
        Args:
            languages: List of {name, color, usage_count} dicts.
        """
        self.languages = languages
        
    def calculate_base_color(self) -> ColorRGB:
        """
        Calculate weighted average color from top languages.
        
        Returns:
            Base color for the aura.
        """
        if not self.languages:
            return ColorRGB.from_hex(self.DEFAULT_COLORS[0])
        
        total_usage = sum(lang.get("usage_count", 1) for lang in self.languages[:3])
        if total_usage == 0:
            total_usage = 1
            
        # Weighted color averaging
        r_sum, g_sum, b_sum = 0.0, 0.0, 0.0
        
        for lang in self.languages[:3]:
            color = ColorRGB.from_hex(lang.get("color", "#858585"))
            weight = lang.get("usage_count", 1) / total_usage
            
            r_sum += color.r * weight
            g_sum += color.g * weight
            b_sum += color.b * weight
            
        return ColorRGB(r_sum, g_sum, b_sum)
    
    def generate_palette(self, num_colors: int = 5) -> list[ColorRGB]:
        """
        Generate a harmonious palette based on the base color.
        
        Args:
            num_colors: Number of colors in palette.
            
        Returns:
            List of ColorRGB colors.
        """
        base = self.calculate_base_color()
        palette = [base]
        
        # Add lighter and darker variants
        palette.append(base.lighten(0.3))
        palette.append(base.darken(0.2))
        
        # Add complementary-ish colors by rotating hue
        # Simple approximation: shift RGB channels
        if num_colors > 3:
            shifted = ColorRGB(
                r=base.g * 0.7 + base.r * 0.3,
                g=base.b * 0.7 + base.g * 0.3,
                b=base.r * 0.7 + base.b * 0.3
            )
            palette.append(shifted)
            
        if num_colors > 4:
            palette.append(shifted.lighten(0.2))
            
        return palette[:num_colors]


class SVGRenderer:
    """
    Renders particle paths as SVG with effects and animations.
    """
    
    def __init__(
        self,
        width: int = 800,
        height: int = 800,
        background_color: str = "#0d1117"
    ):
        """
        Initialize SVG renderer.
        
        Args:
            width: SVG width in pixels.
            height: SVG height in pixels.
            background_color: Background fill color.
        """
        self.width = width
        self.height = height
        self.background_color = background_color
        self.dwg: Optional[Drawing] = None
        
    def create_drawing(self, filename: str = "aura.svg") -> Drawing:
        """
        Create new SVG drawing with dark background.
        
        Args:
            filename: Output filename.
            
        Returns:
            svgwrite Drawing object.
        """
        self.dwg = svgwrite.Drawing(
            filename,
            size=(f"{self.width}px", f"{self.height}px"),
            viewBox=f"0 0 {self.width} {self.height}"
        )
        
        # Add background
        self.dwg.add(self.dwg.rect(
            insert=(0, 0),
            size=(self.width, self.height),
            fill=self.background_color
        ))
        
        return self.dwg
    
    def add_glow_filter(
        self, 
        filter_id: str, 
        intensity: float, 
        color: ColorRGB
    ) -> None:
        """
        Add Gaussian blur glow filter.
        
        Args:
            filter_id: Unique filter ID.
            intensity: Blur intensity (maps to stdDeviation).
            color: Glow color.
        """
        if self.dwg is None:
            raise ValueError("Drawing not initialized. Call create_drawing first.")
        
        # Map intensity (0-1) to blur radius (2-15)
        blur_radius = 2 + intensity * 13
        
        # Create filter with glow effect
        glow_filter = self.dwg.defs.add(self.dwg.filter(
            id=filter_id,
            x="-50%", y="-50%",
            width="200%", height="200%"
        ))
        
        # Gaussian blur
        glow_filter.feGaussianBlur(
            in_="SourceGraphic",
            stdDeviation=blur_radius,
            result="blur"
        )
        
        # Color matrix to tint the blur
        glow_filter.feColorMatrix(
            in_="blur",
            type="matrix",
            values=f"{color.r} 0 0 0 0  "
                   f"0 {color.g} 0 0 0  "
                   f"0 0 {color.b} 0 0  "
                   f"0 0 0 1 0",
            result="coloredBlur"
        )
        
        # Merge original with blur
        merge = glow_filter.feMerge()
        merge.feMergeNode(in_="coloredBlur")
        merge.feMergeNode(in_="SourceGraphic")
    
    def add_gradient(
        self,
        gradient_id: str,
        colors: list[ColorRGB],
        gradient_type: str = "radial"
    ) -> None:
        """
        Add gradient definition.
        
        Args:
            gradient_id: Unique gradient ID.
            colors: List of colors for gradient stops.
            gradient_type: 'linear' or 'radial'.
        """
        if self.dwg is None:
            raise ValueError("Drawing not initialized.")
        
        if gradient_type == "radial":
            gradient = self.dwg.radialGradient(
                id=gradient_id,
                center=("50%", "50%"),
                r="50%"
            )
        else:
            gradient = self.dwg.linearGradient(
                id=gradient_id,
                start=("0%", "0%"),
                end=("100%", "100%")
            )
        
        # Add color stops
        for i, color in enumerate(colors):
            offset = i / (len(colors) - 1) if len(colors) > 1 else 0
            gradient.add_stop_color(
                offset=offset,
                color=color.to_hex()
            )
            
        self.dwg.defs.add(gradient)
    
    def path_to_svg_d(self, path: list[tuple[float, float]]) -> str:
        """
        Convert path coordinates to SVG path 'd' attribute.
        Uses quadratic bezier curves for smooth lines.
        
        Args:
            path: List of (x, y) coordinates.
            
        Returns:
            SVG path 'd' string.
        """
        if len(path) < 2:
            return ""
        
        # Start with move to first point
        d = f"M {path[0][0]:.2f} {path[0][1]:.2f}"
        
        if len(path) == 2:
            # Simple line
            d += f" L {path[1][0]:.2f} {path[1][1]:.2f}"
            return d
        
        # Use smooth quadratic bezier through points
        # Start with line to second point
        d += f" L {path[1][0]:.2f} {path[1][1]:.2f}"
        
        # Quadratic bezier through remaining points
        for i in range(2, len(path)):
            # Control point is the previous point
            # End point is midpoint to next (or current for last)
            if i < len(path) - 1:
                end_x = (path[i][0] + path[i + 1][0]) / 2
                end_y = (path[i][1] + path[i + 1][1]) / 2
            else:
                end_x = path[i][0]
                end_y = path[i][1]
                
            d += f" Q {path[i - 1][0]:.2f} {path[i - 1][1]:.2f} {end_x:.2f} {end_y:.2f}"
        
        return d
    
    def render_paths(
        self,
        paths_with_opacity: list[tuple[list[tuple[float, float]], float]],
        palette: list[ColorRGB],
        glow_intensity: float = 0.5,
        stroke_width_base: float = 1.5
    ) -> None:
        """
        Render particle paths to the SVG.
        
        Args:
            paths_with_opacity: List of (path, opacity) tuples.
            palette: Color palette for strokes.
            glow_intensity: Intensity of glow effect.
            stroke_width_base: Base stroke width.
        """
        if self.dwg is None:
            raise ValueError("Drawing not initialized.")
        
        # Add glow filter
        primary_color = palette[0] if palette else ColorRGB(0.5, 0.7, 1.0)
        self.add_glow_filter("aura-glow", glow_intensity, primary_color)
        
        # Create group for all paths
        paths_group = self.dwg.g(
            id="aura-paths",
            filter="url(#aura-glow)"
        )
        
        # Render each path
        for i, (path, opacity) in enumerate(paths_with_opacity):
            if len(path) < 2:
                continue
                
            # Select color from palette with variation
            color_idx = i % len(palette)
            color = palette[color_idx]
            
            # Slight color variation for visual interest
            variation = np.sin(i * 0.1) * 0.1
            varied_color = color.lighten(max(0, variation)).darken(max(0, -variation))
            
            # Calculate stroke width based on path length
            path_length = len(path)
            stroke_width = stroke_width_base * (0.5 + (path_length / 200))
            stroke_width = min(stroke_width, 3.0)
            
            # Create path element
            d = self.path_to_svg_d(path)
            if d:
                path_elem = self.dwg.path(
                    d=d,
                    stroke=varied_color.to_hex(),
                    stroke_width=stroke_width,
                    stroke_opacity=opacity * 0.8,
                    fill="none",
                    stroke_linecap="round",
                    stroke_linejoin="round"
                )
                paths_group.add(path_elem)
        
        self.dwg.add(paths_group)
    
    def add_center_glow(
        self,
        color: ColorRGB,
        intensity: float
    ) -> None:
        """
        Add central radial glow effect.
        
        Args:
            color: Glow color.
            intensity: Glow intensity.
        """
        if self.dwg is None:
            raise ValueError("Drawing not initialized.")
        
        cx, cy = self.width / 2, self.height / 2
        radius = min(self.width, self.height) * 0.4
        
        # Create radial gradient
        gradient_id = "center-glow-gradient"
        gradient = self.dwg.radialGradient(
            id=gradient_id,
            center=("50%", "50%"),
            r="50%"
        )
        
        # Gradient from color to transparent
        gradient.add_stop_color(0, color.to_hex(), opacity=0.3 * intensity)
        gradient.add_stop_color(0.5, color.to_hex(), opacity=0.1 * intensity)
        gradient.add_stop_color(1, color.to_hex(), opacity=0)
        
        self.dwg.defs.add(gradient)
        
        # Add glow circle
        glow_circle = self.dwg.circle(
            center=(cx, cy),
            r=radius,
            fill=f"url(#{gradient_id})"
        )
        
        # Insert after background but before paths
        self.dwg.add(glow_circle)
    
    def add_animation(self) -> None:
        """Add subtle rotation animation to the aura."""
        if self.dwg is None:
            raise ValueError("Drawing not initialized.")
        
        # Add CSS animation for subtle pulsing
        style = self.dwg.style("""
            @keyframes pulse {
                0%, 100% { opacity: 0.8; }
                50% { opacity: 1; }
            }
            @keyframes rotate {
                from { transform: rotate(0deg); }
                to { transform: rotate(360deg); }
            }
            #aura-paths {
                animation: pulse 4s ease-in-out infinite;
                transform-origin: center;
            }
        """)
        self.dwg.defs.add(style)
    
    def save(self, filename: Optional[str] = None) -> str:
        """
        Save the SVG to file.
        
        Args:
            filename: Optional override filename.
            
        Returns:
            Saved filename.
        """
        if self.dwg is None:
            raise ValueError("Drawing not initialized.")
        
        if filename:
            self.dwg.filename = filename
            
        self.dwg.save()
        return self.dwg.filename


def render_aura(
    paths_with_opacity: list[tuple[list[tuple[float, float]], float]],
    languages: list[dict],
    glow_intensity: float,
    output_path: str = "aura.svg",
    width: int = 800,
    height: int = 800,
    animate: bool = True
) -> str:
    """
    High-level function to render a complete aura SVG.
    
    Args:
        paths_with_opacity: Particle paths from generative engine.
        languages: Language data for color palette.
        glow_intensity: Glow effect intensity (0-1).
        output_path: Output SVG file path.
        width: SVG width.
        height: SVG height.
        animate: Whether to add animation.
        
    Returns:
        Path to saved SVG file.
    """
    # Generate color palette
    palette_gen = ColorPaletteGenerator(languages)
    palette = palette_gen.generate_palette(5)
    base_color = palette_gen.calculate_base_color()
    
    # Create renderer
    renderer = SVGRenderer(width, height)
    renderer.create_drawing(output_path)
    
    # Add central glow first (behind paths)
    renderer.add_center_glow(base_color, glow_intensity)
    
    # Render particle paths
    renderer.render_paths(
        paths_with_opacity,
        palette,
        glow_intensity=glow_intensity
    )
    
    # Add animation if requested
    if animate:
        renderer.add_animation()
    
    # Save and return path
    return renderer.save(output_path)
