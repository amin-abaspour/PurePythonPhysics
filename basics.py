class Vector:
  def __init__(self, *components):
    """Initialize a vector with its components."""
    self.components = components

  def __repr__(self):
    """Unambiguous string representation of the vector."""
    return f"Vector{self.components}"

  def __add__(self, other):
    """Add two vectors."""
    if len(self.components) != len(other.components):
      raise ValueError("Vectors must have the same dimensions to add.")
    added_components = tuple(a + b for a, b in zip(self.components, other.components))
    return Vector(*added_components)

  def __sub__(self, other):
    """Subtract one vector from another."""
    if len(self.components) != len(other.components):
      raise ValueError("Vectors must have the same dimensions to subtract.")
    subtracted_components = tuple(a - b for a, b in zip(self.components, other.components))
    return Vector(*subtracted_components)

  def __mul__(self, scalar):
    """Multiply vector by a scalar."""
    multiplied_components = tuple(a * scalar for a in self.components)
    return Vector(*multiplied_components)

  def __rmul__(self, scalar):
    """Support scalar multiplication from the left."""
    return self.__mul__(scalar)

  def __truediv__(self, scalar):
    """Divide vector by a scalar."""
    if scalar == 0:
      raise ValueError("Cannot divide by zero.")
    divided_components = tuple(a / scalar for a in self.components)
    return Vector(*divided_components)

  def magnitude(self):
      """Calculate the magnitude (length) of the vector."""
      return (sum(a**2 for a in self.components))**(0.5)

  def normalize(self):
    """Return a normalized version of the vector."""
    mag = self.magnitude()
    if mag == 0:
      raise ValueError("Cannot normalize the zero vector.")
    normalized_components = tuple(a / mag for a in self.components)
    return Vector(*normalized_components)

  def dot(self, other):
      """Calculate the dot product with another vector."""
      if len(self.components) != len(other.components):
          raise ValueError("Vectors must have the same dimensions for dot product.")
      return sum(a * b for a, b in zip(self.components, other.components))

  def cross(self, other):
    """Calculate the cross product with another vector (3D vectors only)."""
    if len(self.components) != 3 or len(other.components) != 3:
      raise ValueError("Cross product is defined only for 3-dimensional vectors.")
    a1, a2, a3 = self.components
    b1, b2, b3 = other.components
    cross_components = (
      a2 * b3 - a3 * b2,
      a3 * b1 - a1 * b3,
      a1 * b2 - a2 * b1
    )
    return Vector(*cross_components)

  def angle_with(self, other):
    """Calculate the angle between this vector and another in radians."""
    dot_prod = self.dot(other)
    mags = self.magnitude() * other.magnitude()
    if mags == 0:
      raise ValueError("Cannot calculate angle with zero vector.")
    # Clamp the cosine value to the valid range to avoid numerical errors
    cos_angle = max(min(dot_prod / mags, 1), -1)
    # return math.acos(cos_angle)

  def projection_onto(self, other):
    """Project this vector onto another vector."""
    other_normalized = other.normalize()
    projection_length = self.dot(other_normalized)
    return other_normalized * projection_length



v1 = Vector(1, 2, 3)
v2 = Vector(4, 5, 6)

mag_v1 = v1.magnitude()
print(mag_v1)  # Output: 3.7416573867739413

v1_normalized = v1.normalize()
print(v1_normalized)
# Output: Vector(0.2672612419124244, 0.5345224838248488, 0.8017837257372732)

dot_product = v1.dot(v2)
print(dot_product)  # Output: 32

v7 = v1.cross(v2)
print(v7)  # Output: Vector(-3, 6, -3)


def gravitational_force(m1, m2, position1, position2):
    """Calculate the gravitational force vector exerted on m1 by m2."""
    G = 6.67430e-11  # m^3 kg^-1 s^-2
    displacement = position2 - position1
    distance = displacement.magnitude()
    if distance == 0:
        raise ValueError("Positions must be different to calculate gravitational force.")
    force_magnitude = G * m1 * m2 / distance**2
    force_vector = displacement.normalize() * force_magnitude
    return force_vector

mass1 = 5.972e24  # Mass of Earth in kg
mass2 = 7.348e22  # Mass of Moon in kg
pos_earth = Vector(0, 0, 0)
pos_moon = Vector(384400000, 0, 0)  # Distance from Earth to Moon in meters

force = gravitational_force(mass1, mass2, pos_earth, pos_moon)
print(force)
# Output: Vector(1.982110729079252e+20, 0.0, 0.0)


