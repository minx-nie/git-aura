"""
Git-Aura: Generative Engine Module
Implements particle systems, vector flow fields, and noise functions
for procedural aura generation.
"""

import numpy as np
from opensimplex import OpenSimplex
from typing import NamedTuple
from dataclasses import dataclass, field


class Vector2D(NamedTuple):
    """2D Vector representation."""
    x: float
    y: float
    
    def __add__(self, other: "Vector2D") -> "Vector2D":
        return Vector2D(self.x + other.x, self.y + other.y)
    
    def __mul__(self, scalar: float) -> "Vector2D":
        return Vector2D(self.x * scalar, self.y * scalar)
    
    def magnitude(self) -> float:
        return np.sqrt(self.x ** 2 + self.y ** 2)
    
    def normalize(self) -> "Vector2D":
        mag = self.magnitude()
        if mag == 0:
            return Vector2D(0, 0)
        return Vector2D(self.x / mag, self.y / mag)


@dataclass
class Particle:
    """A particle in the flow field system."""
    position: Vector2D
    velocity: Vector2D = field(default_factory=lambda: Vector2D(0, 0))
    path: list[Vector2D] = field(default_factory=list)
    opacity: float = 1.0
    
    def update(self, acceleration: Vector2D, max_speed: float = 2.0) -> None:
        """
        Update particle position based on acceleration.
        
        Args:
            acceleration: Force to apply to particle.
            max_speed: Maximum velocity magnitude.
        """
        # Update velocity with acceleration
        new_vx = self.velocity.x + acceleration.x
        new_vy = self.velocity.y + acceleration.y
        
        # Clamp to max speed
        speed = np.sqrt(new_vx ** 2 + new_vy ** 2)
        if speed > max_speed:
            new_vx = (new_vx / speed) * max_speed
            new_vy = (new_vy / speed) * max_speed
            
        self.velocity = Vector2D(new_vx, new_vy)
        
        # Update position
        new_pos = Vector2D(
            self.position.x + self.velocity.x,
            self.position.y + self.velocity.y
        )
        self.path.append(self.position)
        self.position = new_pos


class NoiseGenerator:
    """
    Simplex noise generator for organic flow field creation.
    Uses OpenSimplex for smooth, natural-looking gradients.
    """
    
    def __init__(self, seed: int = 0):
        """
        Initialize noise generator with seed.
        
        Args:
            seed: Random seed for deterministic noise generation.
        """
        self.seed = seed
        self.noise = OpenSimplex(seed=seed)
        
    def noise2d(self, x: float, y: float, scale: float = 0.01) -> float:
        """
        Get 2D noise value at coordinates.
        
        Args:
            x: X coordinate.
            y: Y coordinate.
            scale: Noise frequency scale.
            
        Returns:
            Noise value in range [-1, 1].
        """
        return self.noise.noise2(x * scale, y * scale)
    
    def noise3d(self, x: float, y: float, z: float, scale: float = 0.01) -> float:
        """
        Get 3D noise value (useful for animated noise).
        
        Args:
            x: X coordinate.
            y: Y coordinate.
            z: Z coordinate (can represent time).
            scale: Noise frequency scale.
            
        Returns:
            Noise value in range [-1, 1].
        """
        return self.noise.noise3(x * scale, y * scale, z * scale)
    
    def fractal_noise(
        self, 
        x: float, 
        y: float, 
        octaves: int = 4, 
        persistence: float = 0.5,
        scale: float = 0.01
    ) -> float:
        """
        Generate fractal Brownian motion noise (fBm).
        Combines multiple octaves for richer detail.
        
        Args:
            x: X coordinate.
            y: Y coordinate.
            octaves: Number of noise layers.
            persistence: Amplitude decay per octave.
            scale: Base frequency scale.
            
        Returns:
            Combined noise value.
        """
        total = 0.0
        amplitude = 1.0
        frequency = 1.0
        max_value = 0.0
        
        for _ in range(octaves):
            total += amplitude * self.noise2d(x * frequency, y * frequency, scale)
            max_value += amplitude
            amplitude *= persistence
            frequency *= 2.0
            
        return total / max_value


class VectorFlowField:
    """
    Vector flow field for guiding particle movement.
    Creates organic, swirling patterns based on noise functions.
    """
    
    def __init__(
        self,
        width: int,
        height: int,
        seed: int,
        chaos_factor: float = 0.5,
        noise_scale: float = 0.008
    ):
        """
        Initialize the flow field.
        
        Args:
            width: Field width in pixels.
            height: Field height in pixels.
            seed: Random seed for noise generation.
            chaos_factor: 0-1 value controlling turbulence.
            noise_scale: Frequency of noise pattern.
        """
        self.width = width
        self.height = height
        self.noise_gen = NoiseGenerator(seed)
        self.chaos_factor = chaos_factor
        self.noise_scale = noise_scale
        
        # Pre-calculate field resolution
        self.resolution = 10
        self.cols = width // self.resolution
        self.rows = height // self.resolution
        
    def get_force(self, x: float, y: float) -> Vector2D:
        """
        Get the force vector at a given position.
        
        Args:
            x: X coordinate.
            y: Y coordinate.
            
        Returns:
            Force vector at the position.
        """
        # Base angle from noise
        noise_val = self.noise_gen.fractal_noise(
            x, y, 
            octaves=3, 
            persistence=0.6,
            scale=self.noise_scale
        )
        
        # Map noise to angle (0 to 2*PI)
        # Higher chaos = more random angle variation
        base_angle = noise_val * np.pi * 2
        
        # Add secondary turbulence based on chaos factor
        if self.chaos_factor > 0.3:
            turbulence = self.noise_gen.noise2d(
                x * 2, y * 2, 
                scale=self.noise_scale * 3
            )
            base_angle += turbulence * self.chaos_factor * np.pi
        
        # Convert angle to vector
        force_x = np.cos(base_angle)
        force_y = np.sin(base_angle)
        
        # Scale force based on distance from center (creates spiral effect)
        cx, cy = self.width / 2, self.height / 2
        dist_from_center = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        max_dist = np.sqrt(cx ** 2 + cy ** 2)
        radial_factor = 1.0 - (dist_from_center / max_dist) * 0.5
        
        return Vector2D(force_x * radial_factor, force_y * radial_factor)
    
    def get_force_grid(self) -> np.ndarray:
        """
        Generate the complete force field as a numpy array.
        
        Returns:
            Array of shape (rows, cols, 2) containing force vectors.
        """
        grid = np.zeros((self.rows, self.cols, 2))
        
        for row in range(self.rows):
            for col in range(self.cols):
                x = col * self.resolution
                y = row * self.resolution
                force = self.get_force(x, y)
                grid[row, col] = [force.x, force.y]
                
        return grid


class ParticleSystem:
    """
    Particle system that simulates particles flowing through a vector field.
    """
    
    def __init__(
        self,
        flow_field: VectorFlowField,
        num_particles: int,
        particle_density: float = 1.0
    ):
        """
        Initialize particle system.
        
        Args:
            flow_field: Vector flow field to guide particles.
            num_particles: Base number of particles.
            particle_density: Multiplier for particle count (from commit density).
        """
        self.flow_field = flow_field
        self.num_particles = int(num_particles * particle_density)
        self.particles: list[Particle] = []
        self.width = flow_field.width
        self.height = flow_field.height
        
        self._initialize_particles()
        
    def _initialize_particles(self) -> None:
        """Initialize particles in organic distribution around center."""
        cx, cy = self.width / 2, self.height / 2
        
        # Use golden angle for organic spiral distribution
        golden_angle = np.pi * (3 - np.sqrt(5))
        
        for i in range(self.num_particles):
            # Fibonacci spiral distribution
            theta = i * golden_angle
            # Radius grows with sqrt for uniform density
            r = np.sqrt(i / self.num_particles) * min(self.width, self.height) * 0.35
            
            x = cx + r * np.cos(theta)
            y = cy + r * np.sin(theta)
            
            # Add slight randomness
            x += np.random.uniform(-5, 5)
            y += np.random.uniform(-5, 5)
            
            # Opacity based on distance from center
            max_r = min(self.width, self.height) * 0.35
            opacity = 0.3 + 0.7 * (1 - r / max_r)
            
            self.particles.append(Particle(
                position=Vector2D(x, y),
                opacity=opacity
            ))
    
    def simulate(self, steps: int = 100, force_scale: float = 0.5) -> list[Particle]:
        """
        Run particle simulation for given number of steps.
        
        Args:
            steps: Number of simulation steps.
            force_scale: Multiplier for force application.
            
        Returns:
            List of particles with updated paths.
        """
        for step in range(steps):
            for particle in self.particles:
                # Get force from flow field
                force = self.flow_field.get_force(
                    particle.position.x, 
                    particle.position.y
                )
                
                # Scale force
                scaled_force = Vector2D(
                    force.x * force_scale,
                    force.y * force_scale
                )
                
                # Update particle
                particle.update(scaled_force, max_speed=3.0)
                
                # Wrap around edges with slight margin
                margin = 10
                if particle.position.x < -margin:
                    particle.position = Vector2D(
                        self.width + margin, 
                        particle.position.y
                    )
                elif particle.position.x > self.width + margin:
                    particle.position = Vector2D(
                        -margin, 
                        particle.position.y
                    )
                    
                if particle.position.y < -margin:
                    particle.position = Vector2D(
                        particle.position.x, 
                        self.height + margin
                    )
                elif particle.position.y > self.height + margin:
                    particle.position = Vector2D(
                        particle.position.x, 
                        -margin
                    )
                    
        return self.particles
    
    def get_paths(self) -> list[list[tuple[float, float]]]:
        """
        Extract all particle paths as coordinate lists.
        
        Returns:
            List of paths, each path is a list of (x, y) tuples.
        """
        paths = []
        for particle in self.particles:
            if len(particle.path) > 2:
                path = [(p.x, p.y) for p in particle.path]
                paths.append(path)
        return paths
    
    def get_paths_with_opacity(self) -> list[tuple[list[tuple[float, float]], float]]:
        """
        Extract paths with their opacity values.
        
        Returns:
            List of (path, opacity) tuples.
        """
        paths = []
        for particle in self.particles:
            if len(particle.path) > 2:
                path = [(p.x, p.y) for p in particle.path]
                paths.append((path, particle.opacity))
        return paths


class AuraGenerator:
    """
    Main generator class that orchestrates particle system creation
    based on normalized GitHub statistics.
    """
    
    def __init__(
        self,
        width: int = 800,
        height: int = 800,
        seed: int = 0
    ):
        """
        Initialize aura generator.
        
        Args:
            width: Output width in pixels.
            height: Output height in pixels.
            seed: Random seed (typically user ID).
        """
        self.width = width
        self.height = height
        self.seed = seed
        np.random.seed(seed % (2**31))
        
    def generate(
        self,
        density: float,
        chaos_factor: float,
        simulation_steps: int = 150
    ) -> list[tuple[list[tuple[float, float]], float]]:
        """
        Generate aura particle paths.
        
        Args:
            density: Normalized commit density (0-1 from log scale).
            chaos_factor: Normalized chaos factor (0-1 from time variance).
            simulation_steps: Number of simulation iterations.
            
        Returns:
            List of (path, opacity) tuples for rendering.
        """
        # Map density to particle count (50-300 particles)
        base_particles = int(50 + density * 250)
        
        # Map chaos to noise parameters
        noise_scale = 0.005 + chaos_factor * 0.015
        
        # Create flow field
        flow_field = VectorFlowField(
            width=self.width,
            height=self.height,
            seed=self.seed,
            chaos_factor=chaos_factor,
            noise_scale=noise_scale
        )
        
        # Create and run particle system
        particle_system = ParticleSystem(
            flow_field=flow_field,
            num_particles=base_particles,
            particle_density=0.8 + density * 0.4
        )
        
        particle_system.simulate(
            steps=simulation_steps,
            force_scale=0.3 + chaos_factor * 0.4
        )
        
        return particle_system.get_paths_with_opacity()
