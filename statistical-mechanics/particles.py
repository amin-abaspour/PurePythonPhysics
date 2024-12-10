import os
import math
import random
import struct

# -------------------------
# Configuration Constants
# -------------------------
BOX_SIZE = 200           # Size of the box (200x200 pixels)
NUM_PARTICLES = 30       # Number of particles
PARTICLE_RADIUS = 5      # Radius of particles in pixels
TIME_STEP = 1            # Time step for the simulation
NUM_FRAMES = 1000        # Number of frames to simulate
FRAME_DIR = "./frames"   # Directory to save BMP frames

# -------------------------
# Particle Class Definition
# -------------------------
class Particle:
    """Represents a particle with position and velocity."""
    def __init__(self, x, y, vx, vy):
        self.x = x  # X-coordinate
        self.y = y  # Y-coordinate
        self.vx = vx  # Velocity in X
        self.vy = vy  # Velocity in Y

    def update_position(self):
        """Updates the particle's position based on its velocity."""
        self.x += self.vx * TIME_STEP
        self.y += self.vy * TIME_STEP

    def handle_wall_collisions(self):
        """Reverses velocity if particle collides with the walls."""
        if self.x - PARTICLE_RADIUS < 0 or self.x + PARTICLE_RADIUS > BOX_SIZE:
            self.vx *= -1
            self.x = max(PARTICLE_RADIUS, min(self.x, BOX_SIZE - PARTICLE_RADIUS))
        if self.y - PARTICLE_RADIUS < 0 or self.y + PARTICLE_RADIUS > BOX_SIZE:
            self.vy *= -1
            self.y = max(PARTICLE_RADIUS, min(self.y, BOX_SIZE - PARTICLE_RADIUS))

# -------------------------
# Utility Functions
# -------------------------
def create_frames_directory(path):
    """Creates the frames directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)

def initialize_particles():
    """Initializes particles with random positions and velocities."""
    particles = []
    for _ in range(NUM_PARTICLES):
        x = random.uniform(PARTICLE_RADIUS, BOX_SIZE - PARTICLE_RADIUS)
        y = random.uniform(PARTICLE_RADIUS, BOX_SIZE - PARTICLE_RADIUS)
        vx = random.uniform(-1, 1)
        vy = random.uniform(-1, 1)
        particles.append(Particle(x, y, vx, vy))
    return particles

def precompute_circle_mask(radius):
    """Precomputes the relative positions within a circle to optimize rendering."""
    mask = []
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            if dx**2 + dy**2 <= radius**2:
                mask.append((dx, dy))
    return mask

def handle_particle_collisions(particles):
    """Handles elastic collisions between particles."""
    for i in range(len(particles)):
        for j in range(i + 1, len(particles)):
            p1 = particles[i]
            p2 = particles[j]
            dx = p1.x - p2.x
            dy = p1.y - p2.y
            distance = math.hypot(dx, dy)
            if distance < 2 * PARTICLE_RADIUS:
                # Normalize the collision vector
                if distance == 0:
                    # Prevent division by zero; apply a small random displacement
                    angle = random.uniform(0, 2 * math.pi)
                    dx = math.cos(angle)
                    dy = math.sin(angle)
                    distance = 1e-6
                nx = dx / distance
                ny = dy / distance

                # Relative velocity
                dvx = p1.vx - p2.vx
                dvy = p1.vy - p2.vy
                # Dot product of relative velocity and collision normal
                dot = dvx * nx + dvy * ny
                if dot > 0:
                    continue  # Particles are moving away from each other

                # Exchange velocities along the normal direction
                p1.vx -= dot * nx
                p1.vy -= dot * ny
                p2.vx += dot * nx
                p2.vy += dot * ny

                # Adjust positions to prevent overlap
                overlap = 2 * PARTICLE_RADIUS - distance
                p1.x += nx * (overlap / 2)
                p1.y += ny * (overlap / 2)
                p2.x -= nx * (overlap / 2)
                p2.y -= ny * (overlap / 2)

def generate_frame(particles, circle_mask):
    """
    Generates a single frame as raw BMP pixel data.
    Particles are rendered as blue circles on a white background.
    """
    # Initialize image data to white
    image = bytearray([255] * (BOX_SIZE * BOX_SIZE * 3))

    for particle in particles:
        px, py = int(particle.x), int(particle.y)
        for dx, dy in circle_mask:
            x = px + dx
            y = py + dy
            if 0 <= x < BOX_SIZE and 0 <= y < BOX_SIZE:
                index = (y * BOX_SIZE + x) * 3
                # Set pixel to blue (B, G, R)
                image[index:index+3] = b'\xFF\x00\x00'  # Blue in BGR
    return bytes(image)

def save_frame_as_bmp(frame_data, frame_number, output_dir):
    """Saves a single frame as a BMP file with correct padding."""
    file_path = os.path.join(output_dir, f"frame_{frame_number:04d}.bmp")
    
    # BMP Header
    file_size = 54 + (BOX_SIZE * 3 + (4 - (BOX_SIZE * 3) % 4) % 4) * BOX_SIZE
    bmp_header = struct.pack(
        '<2sIHHIIIIHHIIIIII',
        b'BM',                 # Signature
        file_size,             # File size
        0,                     # Reserved1
        0,                     # Reserved2
        54,                    # Pixel data offset
        40,                    # DIB header size
        BOX_SIZE,              # Width
        BOX_SIZE,              # Height
        1,                     # Planes
        24,                    # Bits per pixel
        0,                     # Compression
        (BOX_SIZE * 3 + (4 - (BOX_SIZE * 3) % 4) % 4) * BOX_SIZE,  # Image size
        2835,                  # X pixels per meter
        2835,                  # Y pixels per meter
        0,                     # Total colors
        0                      # Important colors
    )

    # BMP Data with row padding
    padded_row_size = (BOX_SIZE * 3 + 3) & ~3  # Each row is padded to multiple of 4 bytes
    padding = b'\x00' * (padded_row_size - BOX_SIZE * 3)
    bmp_data = bytearray()
    for row in range(BOX_SIZE):
        start = row * BOX_SIZE * 3
        bmp_data += frame_data[start:start + BOX_SIZE * 3] + padding

    # Write BMP file
    with open(file_path, "wb") as bmp_file:
        bmp_file.write(bmp_header + bmp_data)
    print(f"Saved {file_path}")

# -------------------------
# Main Simulation Loop
# -------------------------
def main():
    # Initialize
    create_frames_directory(FRAME_DIR)
    particles = initialize_particles()
    circle_mask = precompute_circle_mask(PARTICLE_RADIUS)
    
    print("Starting simulation...")
    for frame_num in range(1, NUM_FRAMES + 1):
        # Update particle states
        for particle in particles:
            particle.update_position()
            particle.handle_wall_collisions()
        
        handle_particle_collisions(particles)
        
        # Generate and save frame
        frame_data = generate_frame(particles, circle_mask)
        save_frame_as_bmp(frame_data, frame_num, FRAME_DIR)
        
        # Progress update
        if frame_num % 100 == 0 or frame_num == NUM_FRAMES:
            print(f"Frame {frame_num}/{NUM_FRAMES} processed and saved.")
    
    print("Simulation completed.")

if __name__ == "__main__":
    main()
